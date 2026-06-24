#!/usr/bin/env python3
"""PTB Simulation — Flask SSE Backend.  Run: python3 server.py"""
import json, math, time, threading, random
from flask import Flask, Response, jsonify, send_from_directory, request
import os
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'web'))

# Global list to hold frames for the GIF
recording_frames = []


# ── Physics ────────────────────────────────────────────────────────────────
ANOMALY_T  = 90.0
SIM_START  = time.time()
correction_applied_at = [None]   # mutable so threads can share
lock = threading.Lock()

def sim_t():
    return (time.time() - SIM_START) * 3.0   # 3× speed

def delay(t):
    return min(60.0 + (t / 60.0) * 2.0, 480.0)

def nominal(t):
    return dict(
        t=round(t,1),
        range_km=round(55e6 - t*450, 0),
        velocity_ms=round(20500 - t*0.12, 1),
        attitude_deg=round(-3.14*math.sin(t/400), 3),
        gimbal_port_C=round(78 + 0.04*t + 3*math.sin(t/30), 2),
        gimbal_stbd_C=round(76 + 0.02*t + 1.5*math.cos(t/45), 2),
        thrust_pct=round(98.5 - 0.01*t, 2),
        traj_dev=round(0.0, 4),
        hull_psi=14.7,
        power_kw=42.3,
        anomaly=False,
    )

def inject(base, t, corrected):
    dt = t - ANOMALY_T
    decay = math.exp(-(t - correction_applied_at[0]) / 15.0) if corrected else 1.0
    base['gimbal_port_C'] = round(base['gimbal_port_C'] + 12*(1-math.exp(-dt/20))*decay, 2)
    base['thrust_pct']    = round(base['thrust_pct']    - 3.2*(1-math.exp(-dt/25))*decay, 2)
    base['traj_dev']      = round(base['traj_dev']      + 0.04*(1-math.exp(-dt/30))*decay, 4)
    base['anomaly']       = decay > 0.05
    return base

def cabin_state(t):
    s = nominal(t)
    corrected = correction_applied_at[0] is not None
    if t >= ANOMALY_T:
        s = inject(s, t, corrected)
    return s

def predict(recv, m):
    t_base = recv['t']
    t_pred = t_base + 2*m
    p = nominal(t_pred)
    
    # Earth AI propagates forward starting from the received state (which is noisy)
    if recv.get('anomaly'):
        dt_base = t_base - ANOMALY_T
        dt_pred = t_pred - ANOMALY_T
        
        # Calculate expected change from t_base to t_pred based on Earth's estimation model (mismatch: 10 vs 12, etc.)
        delta_temp_base = 10.0 * (1.0 - math.exp(-dt_base / 20.0))
        delta_temp_pred = 10.0 * (1.0 - math.exp(-dt_pred / 20.0))
        temp_change = delta_temp_pred - delta_temp_base
        
        delta_thrust_base = -3.0 * (1.0 - math.exp(-dt_base / 25.0))
        delta_thrust_pred = -3.0 * (1.0 - math.exp(-dt_pred / 25.0))
        thrust_change = delta_thrust_pred - delta_thrust_base
        
        delta_dev_base = 0.035 * (1.0 - math.exp(-dt_base / 30.0))
        delta_dev_pred = 0.035 * (1.0 - math.exp(-dt_pred / 30.0))
        dev_change = delta_dev_pred - delta_dev_base
        
        p['gimbal_port_C'] = round(recv['gimbal_port_C'] + temp_change, 2)
        p['thrust_pct']    = round(recv['thrust_pct'] + thrust_change, 2)
        p['traj_dev']      = round(recv['traj_dev'] + dev_change, 4)
        p['anomaly']       = True
    else:
        # Nominal propagation: track basic nominal changes
        p['gimbal_port_C'] = round(recv['gimbal_port_C'] + 0.04 * (2.0*m), 2)
        p['gimbal_stbd_C'] = round(recv['gimbal_stbd_C'] + 0.02 * (2.0*m), 2)
        p['thrust_pct']    = round(recv['thrust_pct'] - 0.01 * (2.0*m), 2)
        p['traj_dev']      = recv['traj_dev']
    p['t'] = round(t_pred, 1)
    return p

def build_command(pred, m):
    if pred.get('anomaly'):
        return dict(type='CORRECTION',
                    intercept_t=round(pred['t'],1),
                    details=[
                        'THROTTLE: Reduce main engine to 92%',
                        'RCS: +0.4s starboard pulses every 10s',
                        f"GIMBAL: Cool port side — projected {pred['gimbal_port_C']}°C",
                        f"TRAJ: Compensate {pred['traj_dev']:+.4f}% deviation",
                    ])
    return dict(type='NOMINAL', details=['All systems nominal. No action required.'])

def reconcile(cabin, pred, cmd):
    deltas = {k: round(cabin.get(k,0) - pred.get(k,0), 4)
              for k in ('gimbal_port_C','thrust_pct','traj_dev')}
    max_d  = max(abs(v) for v in deltas.values()) if deltas else 0
    safe   = max_d < 0.5
    status = 'RECONCILED' if safe else 'DELTA_HIGH'
    if cmd['type'] == 'CORRECTION':
        rec = ('Earth correction VALIDATED — safe to execute.' if safe
               else f'DELTA HIGH ({max_d:.3f}) — Earth model diverged! Override.')
    else:
        rec = 'Systems nominal. Earth concurs.'
    return dict(status=status, deltas=deltas, safe=safe, recommendation=rec)

# ── SSE stream ────────────────────────────────────────────────────────────
def event_stream():
    try:
        # Initialize dynamic metrics state
        ocli = 22.0
        opfi = 96.0
        ecl = 0.4
        ssa = 99.8
        last_t = None
        
        while True:
            t = sim_t()
            m = delay(t)
            
            # Handle timeline reset detection
            if last_t is None or t < last_t:
                ocli = 22.0
                opfi = 96.0
                ecl = 0.4
                ssa = 99.8
                dt_step = 0.5
            else:
                dt_step = t - last_t
            last_t = t

            t_recv = max(0, t - m)
            
            # Add measurement noise to the telemetry received by Earth
            recv_clean = cabin_state(t_recv)
            recv = dict(recv_clean)
            if t_recv >= ANOMALY_T:
                recv['gimbal_port_C'] = round(recv['gimbal_port_C'] + random.gauss(0, 0.15), 2)
                recv['gimbal_stbd_C'] = round(recv['gimbal_stbd_C'] + random.gauss(0, 0.10), 2)
                recv['thrust_pct']    = round(recv['thrust_pct']    + random.gauss(0, 0.08), 2)
                recv['traj_dev']      = round(recv['traj_dev']      + random.gauss(0, 0.001), 4)
            else:
                recv['gimbal_port_C'] = round(recv['gimbal_port_C'] + random.gauss(0, 0.05), 2)
                recv['gimbal_stbd_C'] = round(recv['gimbal_stbd_C'] + random.gauss(0, 0.05), 2)
                recv['thrust_pct']    = round(recv['thrust_pct']    + random.gauss(0, 0.04), 2)
                recv['traj_dev']      = round(recv['traj_dev']      + random.gauss(0, 0.0002), 4)

            pred   = predict(recv, m)
            cmd    = build_command(pred, m)
            cab    = cabin_state(t)
            recon  = reconcile(cab, pred, cmd)

            # Calculate metrics dynamically based on reconciliation FSM
            max_d = max(abs(v) for v in recon['deltas'].values()) if recon['deltas'] else 0
            safe = recon['safe']
            
            if not safe:  # DELTA_HIGH state (blocked)
                ocli_target = 75.0
                ecl_target = 2.0 * m
                ssa_target = max(60.0, 99.5 - max_d * 50.0)
                opfi_target = max(65.0, 95.0 - max_d * 30.0)
            elif correction_applied_at[0] is not None:  # RECONCILED after correction
                ocli_target = 18.0
                ecl_target = 0.5
                ssa_target = 99.9
                opfi_target = 99.0
            else:  # Nominal RECONCILED state
                ocli_target = 22.0
                ecl_target = 0.4
                ssa_target = 99.8
                opfi_target = 96.0
                
            # Filter dynamics (exponential decay towards target states)
            alpha_ocli = 1.0 - math.exp(-dt_step / 15.0)
            alpha_ecl  = 1.0 - math.exp(-dt_step / 8.0)
            alpha_ssa  = 1.0 - math.exp(-dt_step / 10.0)
            alpha_opfi = 1.0 - math.exp(-dt_step / 12.0)
            
            ocli += (ocli_target - ocli) * alpha_ocli
            ecl  += (ecl_target - ecl) * alpha_ecl
            ssa  += (ssa_target - ssa) * alpha_ssa
            opfi += (opfi_target - opfi) * alpha_opfi
            
            # Add minor Gaussian fluctuations to final reported metrics
            ocli_noise = max(10.0, min(100.0, ocli + random.gauss(0, 0.4)))
            opfi_noise = max(10.0, min(100.0, opfi + random.gauss(0, 0.3)))
            ssa_noise  = max(10.0, min(100.0, ssa + random.gauss(0, 0.1)))
            ecl_noise  = max(0.1, min(100.0, ecl + random.gauss(0, 0.02)))
            
            metrics = dict(
                ocli=round(ocli_noise, 1),
                opfi=round(opfi_noise, 1),
                ecl=round(ecl_noise, 2),
                ssa=round(ssa_noise, 2)
            )

            payload = json.dumps(dict(
                t=round(t,1), m=round(m,1),
                earth=dict(received=recv, predicted=pred, command=cmd),
                mars=dict(cabin=cab, reconciliation=recon),
                metrics=metrics,
                correction_applied=correction_applied_at[0] is not None,
            ))
            yield f"data: {payload}\n\n"
            time.sleep(0.5)
    except GeneratorExit:
        pass

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.route('/correct', methods=['POST'])
def correct():
    with lock:
        if correction_applied_at[0] is None:
            correction_applied_at[0] = sim_t()
    return jsonify(ok=True)

@app.route('/api/reset', methods=['POST', 'GET'])
def api_reset():
    global SIM_START
    with lock:
        SIM_START = time.time()
        correction_applied_at[0] = None
    return jsonify(ok=True, message="Simulation timeline reset successfully.")

@app.route('/api/export_graphs', methods=['POST'])
def api_export_graphs():
    try:
        import generate_plots
        result = generate_plots.generate_analytics()
        return jsonify(ok=True, message=result["message"])
    except Exception as e:
        return jsonify(ok=False, message=str(e)), 500

@app.route('/api/record_frame', methods=['POST'])
def api_record_frame():
    data = request.json
    if not data or 'image' not in data:
        return jsonify(ok=False), 400
    
    header, encoded = data['image'].split(",", 1)
    img_data = base64.b64decode(encoded)
    img = Image.open(BytesIO(img_data)).convert('RGB')
    
    # Scale down by 25% (0.75 ratio) to keep GIF size manageable
    width, height = img.size
    img = img.resize((int(width * 0.75), int(height * 0.75)), Image.Resampling.LANCZOS)
    
    recording_frames.append(img)
    return jsonify(ok=True)

@app.route('/api/stop_recording', methods=['POST'])
def api_stop_recording():
    global recording_frames
    if not recording_frames:
        return jsonify(ok=False, message="No frames recorded"), 400
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"simulation_record_{timestamp}.gif"
    out_path = os.path.join(os.path.dirname(__file__), '..', 'paper', filename)
    
    recording_frames[0].save(
        out_path,
        save_all=True,
        append_images=recording_frames[1:],
        duration=250, # 250ms per frame
        loop=0
    )
    
    recording_frames.clear()
    return jsonify(ok=True, message=f"GIF saved to paper/{filename}", filename=filename)


@app.route('/')
def index():
    # Automatically reset simulation when loading the page
    api_reset()
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'web'), 'index.html')

if __name__ == '__main__':
    print("PTB Simulation running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)

