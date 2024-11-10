import os
import glob

# to import all files in flask/controllers directory without manually importing them
__all__=[os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py")]