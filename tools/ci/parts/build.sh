#!/bin/sh

note "Entry for CI build phase"

test -n "$1" || set -- $BUILD_STEPS
while test -n "$1"; do case "$1" in

    dev ) lib_load main; main_debug

        note "Pd version:"
        # FIXME: pd alias
        # TODO: Pd requires user-conf.
        (
          pd version || noop
          projectdir.sh version || noop
          ./projectdir.sh version || noop
        )
        #note "Pd help:"
        # FIXME: "Something wrong with pd/std__help"
        #(
        #  ./projectdir.sh help || noop
        #)
        #./projectdir.sh test bats-specs bats

        # TODO install again? note "gtasks:"
        #./gtasks || noop

        note "Htd script:"
        (
          htd script
        ) && note "ok" || noop

        note "Pd/Make test:"
        #( test -n "$PREFIX" && ( ./configure.sh $PREFIX && ENV=$ENV ./install.sh ) || printf "" ) && make test
        (
          ./configure.sh && make build test
        ) || noop

        note "basename-reg:"
        (
          ./basename-reg ffnnec.py
        ) || noop
        note "mimereg:"
        (
          ./mimereg ffnenc.py
        ) || noop

        note "lst names local:"
        #892.2 https://travis-ci.org/dotmpe/script-mpe/jobs/191996789
        (
          lst names local
        ) || noop
        # [lst.bash:names] Warning: No 'watch' backend
        # [lst.bash:names] Resolved ignores to '.bzrignore etc:droppable.globs
        # etc:purgeable.globs .gitignore .git/info/exclude'
        #/home/travis/bin/lst: 1: exec: 10: not found
      ;;

    jekyll )
        bundle exec jekyll build
      ;;

    test )
        lib_load build

        ## start with essential tests

        failed=build/test-results-failed.list

        test -n "$TEST_RESULTS" || TEST_RESULTS=build/test-results-speqs.tap
        SUITE="$REQ_SPECS" test_shell $TEST_SHELL $(which bats)

        test "$SHIPPABLE" != "true" ||
          perl $(which tap-to-junit-xml) --input $TEST_RESULTS \
            --output $(basepath $TEST_RESULTS .tap .xml)

        ## Other tests
        #failed=build/test-results-dev.list
        #test -n "$TEST_RESULTS" || TEST_RESULTS=build/test-results-speqs.tap
        #SUITE=$TEST_SPECS test_shell "$TEST_SHELL bats"
        #test "$SHIPPABLE" != "true" ||
        #  perl $(which tap-to-junit-xml) --input $TEST_RESULTS \
        #    --output $(basepath $TEST_RESULTS .tap .xml)

        #test_features

        test -e "$failed" && {
          echo "Failed: $(echo $(cat $failed))"
          rm $failed
          unset failed
          exit 1
        }

      ;;

    noop )
        # TODO: make sure nothing, or as little as possible has been installed
        note "Empty step ($1)" 0
      ;;

    * )
        error "Unknown step '$1'" 1
      ;;

  esac

  note "Step '$1' done"
  shift 1
done

note "Done"
