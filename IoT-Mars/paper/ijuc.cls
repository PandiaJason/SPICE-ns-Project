\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ijuc}[10/12/2004 v0.2 IJUC]
\LoadClass[twoside]{article}

\setlength{\textwidth}{108mm}
\setlength{\textheight}{180mm}
\oddsidemargin 30mm
\setlength{\parindent}{4.25mm}
\setlength{\parskip}{0mm}
\renewcommand{\baselinestretch}{1.1}  % approx 13pt leading
\setcounter{secnumdepth}{2} % number first and second level headings
\bibliographystyle{ijuc}

% Times font
% These three commands make up the entire times.sty package.
\renewcommand{\sfdefault}{phv}
\renewcommand{\rmdefault}{ptm}
\renewcommand{\ttdefault}{pcr}
% enable Times now 
\normalfont\selectfont


%===================
%  title section  (adapted from LLNCS)
%===================

\newcounter{@inst}
%\newcounter{@auth}

\def\institute#1{\gdef\@institute{#1}}
\def\email#1{\unskip\footnote{email: {\tt#1}}{~}}
\def\inst#1{\unskip$^{#1}$}

\def\institutename{\par
 \begingroup
 \parskip=\z@
 \parindent=\z@
 \setcounter{@inst}{1}%
 \def\and{\par\stepcounter{@inst}%
 \noindent$^{\the@inst}$\enspace\ignorespaces}%
 \setbox0=\vbox{\def\thanks##1{}\@institute}%
 \ifnum\c@@inst=1\relax
   \gdef\fnnstart{0}%
 \else
   \xdef\fnnstart{\c@@inst}%
   \setcounter{@inst}{1}%
   \noindent$^{\the@inst}$\enspace
 \fi
 \ignorespaces
 \@institute\par
 \endgroup}


\def\received{}

\def\@maketitle{%
  \def\and{\unskip, }
  \newpage
  \begin{center}%
    \phantom{\rule{0pt}{10mm}}
    {\Large \bfseries\boldmath\@title \par}\vskip 8mm
    \textsc{\@author}\vskip 1mm
    {\small\textit{\institutename}
      \vskip 3mm
      \received\vskip13.5mm}
  \end{center}%
}

\renewenvironment{abstract}{%
  \renewcommand{\baselinestretch}{1.0}\normalsize
  \begin{quote}
}{\end{quote}}

\def\keywords#1{%
  \renewcommand{\baselinestretch}{1.0}\small
  \vskip 2mm
  \begin{quote}\textit{Key words:} #1\end{quote}
  \vskip 2mm
  \renewcommand{\baselinestretch}{1.1}\normalsize
}

%===================
%  figure/table captions: small font, normal leading, 5mm before, 10mm after
%     FIGURE/TABLE nn
%     caption text
%===================

\def\figurename{FIGURE}
\def\tablename{TABLE}
\def\fnum@figure{\figurename~\thefigure}
\def\fnum@table{\tablename~\thetable}


\long\def\@caption#1[#2]#3{
  \@makecaption{\csname fnum@#1\endcsname}{\ignorespaces #3}
}

\long\def\@makecaption#1#2{%
  \vskip 5mm
  \renewcommand{\baselinestretch}{1.0}\small
  {#1}\newline #2\par
  \renewcommand{\baselinestretch}{1.1}\normalsize
  \vskip 6mm
}

%===================
%  figure/table captions: small font, normal leading, 5mm before, 10mm after
%     FIGURE/TABLE nn
%     caption text
%===================

\def\@fnsymbol#1{%
  \ensuremath{%
    \ifcase#1
      \or \star
      \or \dagger
      \or \ddagger
      \or \P
      \or \S
      \or ||
      \or \#
      \or \star\star
      \or \dagger\dagger
      \or \ddagger\ddagger
      \or \P\P
      \or \S\S
      \or ||||
      \or \#\#
      \else\@ctrerr\fi
  }
}

\renewcommand\thefootnote{\@fnsymbol\c@footnote}

%===================
%  section: 2 lines before, one after, bold, normal size, all caps
%  subsection: 1 line before, none after, bold, normal size
%  subsection: 1 line before, none after, italic, normal size
%===================

\renewcommand\section{\@startsection{section}{1}{\z@}%
                       {-20\p@ \@plus -4\p@ \@minus -4\p@}%
                       {10\p@ \@plus 4\p@ \@minus 4\p@}%
                       {\normalfont\bfseries\boldmath\MakeUppercase}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
                       {-10\p@ \@plus -4\p@ \@minus -4\p@}%
                       {1\p@ \@plus 1\p@ \@minus 1\p@}%
                       {\normalfont\normalsize\bfseries\boldmath}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                       {-10\p@ \@plus -4\p@ \@minus -4\p@}%
                       {1pt \@plus 1\p@ \@minus 1\p@}%
                       {\normalfont\normalsize\itshape}}


%===================
%  bibliography
%===================

\renewenvironment{thebibliography}[1]{%
  \section*{References}
  \renewcommand{\baselinestretch}{1.0}
  \footnotesize
  \list{%
    \@biblabel{\@arabic\c@enumiv}}%
    {\settowidth\labelwidth{\@biblabel{#1}}%
      \leftmargin\labelwidth
      \advance\leftmargin\labelsep
      \usecounter{enumiv}%
      \let\p@enumiv\@empty
      \renewcommand\theenumiv{\@arabic\c@enumiv}
  }%
}%
{ \endlist
  \renewcommand{\baselinestretch}{1.1}
  \normalsize
}




