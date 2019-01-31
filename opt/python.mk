.PHONY: test* coverage* clean clean-pycache \
inject-readme check-readme git-is-clean \
upload

TOXENVS ?= py

## Testing
test: inject-readme
	tox

# Run tox with coverage report
test-cov: $(patsubst %, test-cov-%, $(TOXENVS))

test-cov-%: inject-readme
	tox -e $* -- --cov $(PROJECT)
	$(MAKE) coverage-report-$*

coverage-report: $(patsubst %, coverage-report-%, $(TOXENVS))

coverage-report-%:
	.tox/$*/bin/coverage combine .coverage
	.tox/$*/bin/coverage report
	.tox/$*/bin/coverage html --directory $(PWD)/.tox/$*/tmp/cov_html

clean: clean-pycache
	rm -rf src/*.egg-info *.egg-info .tox MANIFEST

clean-pycache:
	test -d src && \
		find src -name __pycache__ -o -name '*.pyc' -print0 \
		| xargs --null rm -rf
	rm -rf *.pyc __pycache__

## Inject content of README.rst to the top-level docstring.
inject-readme: $(TOPMODULE)
$(TOPMODULE): README.rst
	sed '1,/^"""$$/d' $@ > $@.tail
	rm $@
	echo '"""' >> $@
	cat README.rst >> $@
	echo '"""' >> $@
	cat $@.tail >> $@
	rm $@.tail
# Note that sed '1,/^"""$/d' prints the lines after the SECOND """
# because the first """ appears at the first line.

# Check that README.rst and $(TOPMODULE) are in the consistent state.
check-readme:
	$(MAKE) git-is-clean
	$(MAKE) --always-make inject-readme
	$(MAKE) git-is-clean

git-is-clean:
	git status --short --untracked-files=no | xargs --no-run-if-empty false

## Upload to PyPI
upload: check-readme
	rm -rf dist/
	python setup.py sdist
	python setup.py bdist_wheel
	twine upload dist/*
