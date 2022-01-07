mkfifo looppipe 2>/dev/null || true
<looppipe python3 wordle.py -q | tee >(python3 solver.py -q | tee looppipe)
