
import glob
import os

environments = set()
files = glob.glob('/srv/greencandle/install/docker-compose*')
for file in files:
    with open(file, 'r') as compose_file:
        lines = compose_file.readlines()
        for line in lines:
            if "CONFIG_ENV" in line:
                environments.add(line.split('=')[-1].rstrip())

#print(environments)

all_envs = os.popen('find /srv/greencandle/config/env -type d').read().split()

all_envs = [x.replace('/srv/greencandle/config/env/','') for x in all_envs]
#print(all_envs)

for env in all_envs:
    if env not in environments:
        print(env)
