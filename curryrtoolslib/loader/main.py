import sys
from . import entry_points

def startup():

    if len(sys.argv) < 2:
        print('No action was specified')
        print('Valid actions: device, trainning')
        sys.exit(1)
    
    action = sys.argv[1]
    if action == 'device':
        entry_points.main_devices()
    elif action == 'trainning':
        entry_points.main_trainning()
    else:
        print('Invalid action: %s' % (action))
        print('Valid actions: device, trainning')
        sys.exit(1)



if __name__ == '__main__':
    startup()
