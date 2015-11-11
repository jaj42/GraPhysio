PROGNAME=	csvbackend

GHC=	ghc
GHCFLAGS=	-threaded -fwarn-unused-imports -O2
#-prof -fprof-auto
SRCS=	main.hs util.hs processtable.hs

all : clean-bin ${PROGNAME}

${PROGNAME} :
	${GHC} ${GHCFLAGS} --make ${SRCS} -o $@

clean:
	@rm *.hi *.o 2>/dev/null || true

clean-bin:
	@rm ${PROGNAME} 2>/dev/null || true
