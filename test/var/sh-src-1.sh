
case "$TEST_EXPR" in

    "$MATCH_1_1" | "$MATCH_1_2" ) printf 1 ;;

    "$MATCH_2_1" | "$MATCH_2_2" ) echo 2 ;;

esac

