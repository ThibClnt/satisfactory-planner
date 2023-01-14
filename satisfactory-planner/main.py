import pygame
from app import Application

pygame.init()

Application((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE).loop()

pygame.quit()
