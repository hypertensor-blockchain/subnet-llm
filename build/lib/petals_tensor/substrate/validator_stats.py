"Run to view RAM and CPU usage"
from tqdm import tqdm
from time import sleep
import psutil

# python3 src/petals/substrate/validator_stats.py

with tqdm(total=100, desc='cpu%', position=1) as cpubar, tqdm(total=100, desc='ram%', position=0) as rambar:
    while True:
        rambar.n=psutil.virtual_memory().percent
        cpubar.n=psutil.cpu_percent()
        rambar.refresh()
        cpubar.refresh()
        sleep(0.5)
