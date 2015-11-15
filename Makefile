GMAKE=gmake

all:
	@$(MAKE) -C csvbackend
	@$(GMAKE) -C frontend
