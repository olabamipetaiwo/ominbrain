


<!-- ls -la /blue/so589980.ucf/$USER/
cd /blue/so589980.ucf/$USER/
pwd -->
-m 


blue_quota -  check storage
sinfo -o "%P %G %D" | grep -i gpu - check GPU
check time - squeue -j 38868089 -o "%L %l %M"