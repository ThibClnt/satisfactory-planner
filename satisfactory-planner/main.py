import pygame
from app import Application

pygame.init()

fullscreen = False
if fullscreen:
    Application((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE).loop()
else:
    Application((540, 540), pygame.RESIZABLE).loop()

pygame.quit()
