#!/usr/bin/env python
from __future__ import division
import pygame, pygame.gfxdraw
import random
import time
import numpy as np
from collections import deque
import bubblepopgame

if __name__ == '__main__':
    import argparse, sys, datetime, os, csv
    parser = argparse.ArgumentParser(description='Bubble Pop game.')
    parser.add_argument('--minsize', type=int, default=20,  help="Minimum bubble size (in pixels)")
    parser.add_argument('--maxsize', type=int, default=100, help="Maximum bubble size (in pixels)")
    parser.add_argument('-f', '--fullscreen', default=False, action='store_true')
    parser.add_argument('-o', '--output-prefix', type=str, default='', metavar='PREFIX', help='Prepend PREFIX to file name')
    args = parser.parse_args()
    if args.minsize >= args.maxsize:
        print >> sys.stderr, 'minsize (%s) must be smaller than maxsize (%s)'  % (args.minsize, args.maxsize)
        sys.exit(1)

    game = bubblepopgame.BubbleGame(bubble_sizes=(args.minsize,args.maxsize), fullscreen=args.fullscreen)

    timestr = datetime.datetime.today().strftime('%d-%m-%y-%H.%M.%f')
    filename = '%s_%s.csv' % (args.output_prefix, timestr)
    csvfile = open(filename, 'w')
    writer = csv.writer(csvfile)
    
    print 'Writing data to', filename
    from math import hypot
    def gather_data(*args):
        d = hypot(*np.array(args[0])-args[1])
        print d, args[5], args[2]
        writer.writerow([d, args[5], args[2]])

    game.movement.connect(gather_data)

    game.run()
    csvfile.close()
