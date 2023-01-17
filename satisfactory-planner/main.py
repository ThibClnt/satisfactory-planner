import pygame
from app import Application
from settings import fullscreen

pygame.init()

if fullscreen:
    Application((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE).loop()
else:
    Application((540, 540), pygame.RESIZABLE).loop()

pygame.quit()
