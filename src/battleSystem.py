import configparser
from ctypes import pointer
from dis import dis
from ensurepip import bootstrap
from faulthandler import disable
from tabnanny import check
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import Tk, Canvas, Frame, BOTH
from random import randint
import math
from PIL import Image, ImageTk
import PIL.Image
import tkinter.ttk as ttk
from functools import partial
import random
import sys,os
from pathlib import Path
import time

from src.shipCombat import *
from src.canvasCalls import *
import src.naglowek as naglowek
from src.rootCommands import *
from src.systems import *
from src.ammunitionType import *

#   Artemis 2021
#   Project by Pawel Golabek
#
#   Used libraries (excluding build-in): Pillow, Pil


#s = ttk.Style()
#s.theme_use('xpnative')
##s.configure("red.Horizontal.TProgressbar", foreground='blue', background='red')

class ui_icons():
    x=10

class _events():
    playerDestroyed = False
    showedWin = False


############################## AMUNITION #############################################



class ship():
    def __init__(self,var, name="MSS Artemis", owner="ai2", target='MSS Artemis',
                 hp=200, maxHp=None, ap=10000, maxAp=None, shields=3, maxShields = 3, xPos=300, yPos=300,energyLimit = 20,
                 ammunitionChoice=0, ammunitionNumberChoice=0, systemSlots = [],systemStatus = [],
                 detectionRange=200, xDir=0.0, yDir=1, turnRate=0.5, ghostPoints = [], signatures = [], speed=40, maxSpeed = 40,
                 outlineColor="red",id = 1,signatureCounter=0):  # replace shot handler
        # Init info                                             ## to handle shots when more than one enemy in range
        self.name = name
        self.owner = owner
        self.target = target
        self.xPos = xPos
        self.yPos = yPos
        self.energyLimit = energyLimit
        self.tmpEnergyLimit = energyLimit
        self.energy = energyLimit
        self.ammunitionChoice = ammunitionChoice
        self.ammunitionNumberChoice = ammunitionNumberChoice

        self.systemSlots = []
        for tmp in systemSlots:
            if(not tmp == 'none'):
                targetClass =  naglowek.systemLookup[tmp]
                tmpSystem = targetClass()
                self.systemSlots.append(tmpSystem)
        i = 0
        for tmp in systemStatus:
            if(i < len(self.systemSlots)):
                self.systemSlots[i].cooldown = int(tmp)
                i+=1
        self.detectionRange = detectionRange
        self.xDir = xDir
        self.yDir = yDir
        self.turnRate = turnRate
        self.ghostPoints = ghostPoints
        self.signatures = signatures
        self.speed = round(float(speed))
        self.maxSpeed = round(float(maxSpeed))
        self.outlineColor = outlineColor
        self.hp = hp
        if(maxHp == None):
            self.maxHp = hp
        else:
            self.maxHp = maxHp
        self.ap = ap
        if(maxAp == None):
            self.maxAp = ap
        else:
            self.maxAp = maxAp
        self.shields = shields
        self.maxShields = maxShields
        self.shieldsState = []
        self.alreadyShot = FALSE
        tmp = 0
        while(tmp < maxShields):
            self.shieldsState.append(var.shieldMaxState)
            tmp += 1
        # Mid-round info
        self.shotsTaken = 0
        self.shotsNotTaken = 0
        self.visible = FALSE
        self.moveOrderX = xPos+0.01
        self.moveOrderY = yPos+0.01
        self.id = id
        self.signatureCounter = 0

class tracer():
    def __init__(self, xPos=300, yPos=300, xDir=0.0, yDir=1.0, turnRate=0.5, speed=40): 
        self.xPos = xPos
        self.yPos = yPos
        self.xDir = xDir
        self.yDir = yDir
        self.turnRate = turnRate
        self.speed = speed
        self.moveOrderX = None
        self.moveOrderY = None

class playerController():
    a = 10

class aiController():
    def systemChoice(ship,ships):
        basicEnergy = 0
        for system in ship.systemSlots:
            system.energy = system.minEnergy
            basicEnergy += system.minEnergy
        systemPool = []
        energy = ship.energyLimit - basicEnergy
        systemChecked = 0
        for system in ship.systemSlots:         # create system pool
            systemMaxPoints = system.maxEnergy
            while(systemMaxPoints > 0):
                systemPool.append(systemChecked)
                systemMaxPoints -= 1
            systemChecked += 1
                                                # add modifiers to pool if neeeded
        while(energy > 0 and len(systemPool)):
            choiceRand = random.randrange(0,len(systemPool))
            choiceNumber = systemPool.pop(choiceRand)
            (ship.systemSlots[choiceNumber]).energy += 1
            energy-=1
                           

    def moveOrderChoice(ship,ships,var,gameRules,uiMetrics):
        checksLeft = 40
        bestOrderX = 100    #default if everything else fails
        bestOrderY = 100    #default if everything else fails
        bestOrderValue = float('-inf')
        while(checksLeft):
            currentOrderValue = random.randint(19000, 21000)
            currentOrderX = ship.xPos + random.randint(-200, 200)
            currentOrderY = ship.yPos + random.randint(-200, 200)
            ship.ghostPoints = []
            currentTracer = tracer()
            currentTracer.xPos = ship.xPos
            currentTracer.yPos = ship.yPos
            currentTracer.xDir = ship.xDir
            currentTracer.yDir = ship.yDir
            currentTracer.turnRate = ship.turnRate
            currentTracer.speed = ship.speed
            currentTracer.moveOrderX = currentOrderX
            currentTracer.moveOrderY = currentOrderY
            currentTracer.ttl = var.turnLength + 800 # +200 to avoid unavoidable collisions next turn
            
            while(True):
                # check for terrain
                if(currentTracer.ttl % 5 == 0):
                    colorWeight = var.mask[int(currentTracer.xPos)][int(currentTracer.yPos)]
                # vector normalisation
                scale = math.sqrt((currentTracer.moveOrderX-currentTracer.xPos)*(currentTracer.moveOrderX-currentTracer.xPos) +
                                    (currentTracer.moveOrderY-currentTracer.yPos)*(currentTracer.moveOrderY-currentTracer.yPos))
                if(scale == 0):
                    scale = 0.01
                # move order into normalised vector
                moveDirX = -(currentTracer.xPos-currentTracer.moveOrderX) / scale
                moveDirY = -(currentTracer.yPos-currentTracer.moveOrderY) / scale

                degree = currentTracer.turnRate
                rotateVector(degree, currentTracer, moveDirX, moveDirY)

                if(colorWeight < 600 and colorWeight > 400):
                    movementPenality = gameRules.movementPenalityMedium
                elif(colorWeight < 400 and colorWeight > 200):
                    movementPenality = gameRules.movementPenalityMedium
                    currentOrderValue -= 400
                elif(colorWeight <= 200):
                    movementPenality = gameRules.movementPenalityHard
                    currentOrderValue -= 4000
                else:
                    movementPenality = 0.000001  # change

                xVector = currentTracer.xDir*currentTracer.speed/360
                yVector = currentTracer.yDir*currentTracer.speed/360

                currentTracer.xPos += xVector - xVector * movementPenality
                currentTracer.yPos += yVector - yVector * movementPenality
                if(0 > currentTracer.xPos):
                    currentTracer.xPos += uiMetrics.canvasWidth
                if(currentTracer.xPos >= uiMetrics.canvasWidth):
                    currentTracer.xPos -= uiMetrics.canvasWidth
                if(0 > currentTracer.yPos):
                    currentTracer.yPos += uiMetrics.canvasHeight
                if(currentTracer.yPos >= uiMetrics.canvasHeight):
                    currentTracer.yPos -= uiMetrics.canvasHeight
                currentTracer.ttl -= 1
                if(not currentTracer.ttl):
                    break
            if(currentOrderValue > bestOrderValue):
                bestOrderX = currentOrderX
                bestOrderY = currentOrderY
                bestOrderValue = currentOrderValue
            del currentTracer
            checksLeft -= 1
            if(checksLeft < 360 and bestOrderValue > 0 or not checksLeft):
                break
        ship.moveOrderX = bestOrderX
        ship.moveOrderY = bestOrderY


    def ammunitionChoiceScale(ship):  # virtual choice for AI Controller
        return 1
    a = 10

################################################ STARTUP ######################################

def manageSystemActivations(ships,var,gameRules,uiMetrics,shipLookup):
    for ship in ships:
        for system in ship.systemSlots:
            system.activate(ship,var,gameRules,uiMetrics)

def manageSystemTriggers(ships,var,shipLookup,uiMetrics):
    for ship1 in ships:
        for system in ship1.systemSlots:
            system.trigger(var,ship1,ships,shipLookup,uiMetrics)
                # trigger is activated during round and activation is between
                                    
def getOrders(ship,var,gameRules,uiMetrics,forced=False):
    tracered = False
    if(ship.owner == "player1"):
        if(var.mouseButton1 and mouseOnCanvas(var,uiMetrics) and var.selection == ship.id):
            ship.moveOrderX = var.left + \
                ((var.pointerX-uiMetrics.canvasX)/var.zoom)
            ship.moveOrderY = var.top + \
                ((var.pointerY-uiMetrics.canvasY)/var.zoom)
            tracered = True
            putTracer(ship,var,gameRules,uiMetrics)
    if(not tracered and ship.owner == "player1" and forced ):
            putTracer(ship,var,gameRules,uiMetrics)

def manageLandmarks(landmarks, ships):
    for landmark in landmarks:
        if(landmark.cooldown > 0):
            landmark.cooldown -= 1
        for ship in ships:
            dist = ((landmark.xPos - ship.xPos)*(landmark.xPos - ship.xPos) +
                    (landmark.yPos - ship.yPos)*(landmark.yPos - ship.yPos))
            if(dist < landmark.radius*landmark.radius and landmark.cooldown == 0):
                getBonus(ship, landmark.boost)
                landmark.cooldown = landmark.defaultCooldown


def getBonus(ship, boost):
    if(boost == 'health'):
        ship.hp += 50
    elif(boost == 'armor'):
        ship.ap += 50
        # add boosts




############################################## MISSLES ##############################################


def manageRockets(missles,shipLookup,var,events,uiElements,uiMetrics):    # manage mid-air munitions
    for missle in missles:
        if(missle.sort == 'laser'):
            putLaser(missle,var,shipLookup)
            dealDamage(shipLookup[missle.target], missle.damage,var)
            checkForKilledShips(events,shipLookup,var,uiElements)
            missles.remove(missle)
            continue
        targetShipX = shipLookup[missle.target].xPos
        targetShipY = shipLookup[missle.target].yPos

        if(missle.xPos == max(missle.xPos,targetShipX)):
            aroundDistance = uiMetrics.canvasWidth - missle.xPos + targetShipX
            straightDistance = missle.xPos - targetShipX
        else:
            aroundDistance = uiMetrics.canvasWidth + missle.xPos - targetShipX
            straightDistance = targetShipX - missle.xPos

        if (straightDistance < aroundDistance):
            minDistX = (targetShipX - missle.xPos)            
        else:
            minDistX = (missle.xPos - targetShipX)
        ##
        if(missle.yPos == max(missle.yPos,targetShipY)):
            aroundDistance = uiMetrics.canvasHeight - missle.yPos + targetShipY
            straightDistance = missle.yPos - targetShipX
        else:
            aroundDistance = uiMetrics.canvasHeight + missle.yPos - targetShipY
            straightDistance = targetShipY - missle.yPos

        if (straightDistance < aroundDistance):
            minDistY = targetShipY - missle.yPos          
        else:
            minDistY = missle.yPos - targetShipY  

        scale = math.sqrt((minDistX) * (minDistX) + minDistY * minDistY)
        if scale == 0:
            scale = 0.01
        minDistX /= scale
        minDistY /= scale
        degree = missle.turnRate
        rotateVector(degree, missle, minDistX, minDistY)
        missle.xPos += missle.xDir*missle.speed/360
        missle.yPos += missle.yDir*missle.speed/360
        if((abs(missle.xPos - targetShipX) *
            abs(missle.xPos - targetShipX) +
            abs(missle.yPos - targetShipY) *
            abs(missle.yPos - targetShipY)) < 25):
            dealDamage(shipLookup[missle.target], missle.damage,var)
            missles.remove(missle)
            continue
        if(0 > missle.xPos):
            missle.xPos += uiMetrics.canvasWidth
        if(missle.xPos > uiMetrics.canvasWidth):
            missle.xPos -= uiMetrics.canvasWidth
        if(0 > missle.yPos):
            missle.yPos += uiMetrics.canvasHeight
        if(missle.yPos > uiMetrics.canvasHeight):
            missle.yPos -= uiMetrics.canvasHeight




def drawLasers(var,canvas,uiMetrics):
    for laser in var.lasers:
        if laser.ttl>0:
            drawX = (laser.xPos - var.left) * var.zoom
            drawY = (laser.yPos - var.top) * var.zoom
         #       
         #   drawX2 = (laser.targetXPos - var.left) * \
         #       var.zoom
         #   drawY2 = (laser.targetYPos - var.top) * \
         #       var.zoom

##############
            aroundFlagX = False
            aroundFlagY = False
            if(laser.xPos == max(laser.xPos,laser.targetXPos)):
                aroundDistance = uiMetrics.canvasWidth - laser.xPos + laser.targetXPos
                laserCloserToRight = True
                straightDistance = laser.xPos - laser.targetXPos
            else:
                aroundDistance = uiMetrics.canvasWidth + laser.xPos - laser.targetXPos
                laserCloserToRight = False
                straightDistance = laser.targetXPos - laser.xPos

            if (straightDistance < aroundDistance):
                x2 = laser.targetXPos
                x3 = laser.xPos
                x4 = laser.targetXPos
            else:
                aroundFlagX = True
                if(laserCloserToRight):
                    x2 = laser.targetXPos + uiMetrics.canvasWidth
                    x3 = laser.xPos - uiMetrics.canvasWidth
                    x4 = laser.targetXPos
                else: 
                    x2 = laser.targetXPos - uiMetrics.canvasWidth
                    x3 = laser.xPos + uiMetrics.canvasWidth
                    x4 = laser.targetXPos
            ##
            if(laser.yPos == max(laser.yPos,laser.targetYPos)):
                aroundDistance = uiMetrics.canvasHeight - laser.yPos + laser.targetYPos
                laserCloserToDown = True
                straightDistance = laser.yPos - laser.targetYPos
            else:
                aroundDistance = uiMetrics.canvasHeight + laser.yPos - laser.targetYPos
                laserCloserToDown = False
                straightDistance = laser.targetYPos - laser.yPos

            if (straightDistance < aroundDistance):
                y2 = laser.targetYPos 
                y3 = laser.yPos
                y4 = laser.targetYPos
            else:
                aroundFlagY = True
                if(laserCloserToDown):
                    y2 = laser.targetYPos + uiMetrics.canvasHeight
                    y3 = laser.yPos - uiMetrics.canvasHeight
                    y4 = laser.targetYPos
                else: 
                    y2 = laser.targetYPos - uiMetrics.canvasHeight
                    y3 = laser.yPos + uiMetrics.canvasHeight
                    y4 = laser.targetYPos

            drawX2 = (x2- var.left) * var.zoom
            drawX3 = (x3- var.left) * var.zoom
            drawX4 = (x4- var.left) * var.zoom

            drawY2 = (y2- var.top) * var.zoom
            drawY3 = (y3- var.top) * var.zoom
            drawY4 = (y4- var.top) * var.zoom

            line = canvas.create_line(drawX,drawY,drawX2,drawY2, fill = laser.color)
            canvas.elements.append(line)
            

            if(aroundFlagX or aroundFlagY):
                line = canvas.create_line(drawX3,drawY3,drawX4,drawY4, fill = laser.color)
                canvas.elements.append(line)
        else:
            (var.lasers).remove(laser)


def update(var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root):        ### sprawdz co zamula
    if(var.drag==''):    
        canvas.delete('all')
        updateScales(uiElements,var,shipLookup)
        if(var.frameTime % 5 == 0):
            updateLabels(uiElements,shipLookup,var)
        updateEnergy(var,uiElements,shipLookup)
        var.gameSpeed = float((uiElements.gameSpeedScale).get())
        if(not var.turnInProgress):
            manageSystemActivations(var.ships,var,gameRules,uiMetrics,shipLookup)
            for ship in var.ships:
                getOrders(ship,var,gameRules,uiMetrics)
        ticksToEndFrame = 0
        if(var.turnInProgress):
            root.title("TURN IN PROGRESS")
            var.systemTime = time.time()
            while(ticksToEndFrame < var.gameSpeed):
                detectionCheck(var,uiMetrics)
                updateShips(var,uiMetrics,gameRules,shipLookup,events,uiElements)
                checkForKilledShips(events,shipLookup,var,uiElements)
                manageLandmarks(var.landmarks,var.ships)
                manageRockets(var.currentMissles,shipLookup,var,events,uiElements,uiMetrics) 
                manageSystemTriggers(var.ships,var,shipLookup,uiMetrics)
                updateShields(var.ships,var)
                updateCooldowns(var.ships,var,shipLookup,uiMetrics)
                updateSignatures(var.ships)
                for laser in var.lasers:
                    if var.turnInProgress:
                        laser.ttl -= 1
                ticksToEndFrame += 1
                uiElements.timeElapsedProgressBar['value'] += 1
                if(uiElements.timeElapsedProgressBar['value'] > var.turnLength):
                    root.title("AI IS THINKING")
                    endTurn(uiElements,var,gameRules,uiMetrics,canvas,ammunitionType,uiIcons)
                    break
        else:
            root.title(uiElements.rootTitle)
        var.input = (var.mouseWheelUp or var.mouseWheelDown or (var.mouseButton3 and var.zoom != 1 and mouseOnCanvas(var,uiMetrics)) or var.mouseButton1 )
        newWindow(uiMetrics,var,canvas)
        drawGhostPoints(canvas,var)
        drawSignatures(canvas,var)
        drawLandmarks(var,canvas,uiIcons)
        drawLasers(var,canvas,uiMetrics)
        drawRockets(var,ammunitionType,canvas)
        var.mouseOnUI = False
        var.mouseWheelUp = False
        var.mouseWheelDown = False
        var.mouseButton1 = False
        var.mouseButton2 = False
        var.zoomChange = False
        drawShips(canvas,var,uiMetrics)
        trackMouse(var)
        var.frameTime+=1
        if(var.finished):
            return
        if(var.updateTimer>0):
            var.updateTimer -= 1
        if(var.turnInProgress or var.mouseButton3):
            root.after(20, partial(update,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root))
        else:
            root.after(20, partial(update,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root))


def newWindow(uiMetrics,var,canvas):
    canvas.delete(canvas.imageID)
    canPoiX = var.pointerX - uiMetrics.canvasX
    canPoiY = var.pointerY - uiMetrics.canvasY
    var.imgg = ImageTk.PhotoImage(var.resizedImage)
    if(not var.mouseWheelUp and not var.mouseWheelDown and var.mouseButton3 and var.zoom != 1 and mouseOnCanvas(var,uiMetrics)):
        if(var.zoom == 1):
            var.mouseX = ((canPoiX + var.pointerDeltaX) + var.left)
            var.mouseY = ((canPoiY + var.pointerDeltaY) + var.top)
        else:
            var.mouseX = ((canPoiX + var.pointerDeltaX) / (var.zoom-1) + var.left)
            var.mouseY = ((canPoiY + var.pointerDeltaY) / (var.zoom-1) + var.top)
        var.yellowX = (uiMetrics.canvasWidth/var.zoom)/2
        var.yellowY = (uiMetrics.canvasHeight/var.zoom)/2

        if(var.mouseX > uiMetrics.canvasWidth - var.yellowX):  # bumpers on sides
            var.mouseX = var.right - var.yellowX
        if(var.mouseX < var.yellowX):
            var.mouseX = var.left + var.yellowX
        if(var.mouseY > uiMetrics.canvasHeight - var.yellowY):
            var.mouseY = var.bottom - var.yellowY
        if(var.mouseY < var.yellowY):
            var.mouseY = var.top + var.yellowY

        var.left = var.mouseX - var.yellowX
        var.right = var.mouseX + var.yellowX
        var.top = var.mouseY - var.yellowY
        var.bottom = var.mouseY + var.yellowY
        var.mouseX = var.right - var.left
        var.mouseY = var.bottom - var.top

        var.resizedImage = (var.image).crop((var.left, var.top, var.right, var.bottom))
        var.resizedImage = (var.resizedImage).resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight), PIL.Image.ANTIALIAS)

        var.imgg = ImageTk.PhotoImage(var.resizedImage)
        canvas.imageID = canvas.create_image(0, 0, image=var.imgg, anchor='nw')


    if((var.mouseWheelUp or var.mouseWheelDown) and mouseOnCanvas(var,uiMetrics) and var.zoomChange):
        var.imgg = var.image
        if(var.mouseWheelUp and var.zoomChange):
            if(var.zoom == 1):
                var.mouseX = (canPoiX)
                var.mouseY = (canPoiY)
            else:
                var.mouseX = ((canPoiX) / (var.zoom) + var.left)
                var.mouseY = ((canPoiY) / (var.zoom) + var.top)

        elif(var.mouseWheelDown):
            var.zoom = 1
            var.left = 0
            var.top = 0
            var.right = uiMetrics.canvasWidth
            var.bottom = uiMetrics.canvasHeight
            var.resizedImage = var.image
            var.imgg = ImageTk.PhotoImage(var.resizedImage)
    
        var.yellowX = (uiMetrics.canvasWidth/var.zoom)/2
        var.yellowY = (uiMetrics.canvasHeight/var.zoom)/2

        if(var.mouseX > uiMetrics.canvasWidth - var.yellowX):  # bumpers on sides
            var.mouseX = var.right - var.yellowX
        if(var.mouseX < var.yellowX):
            var.mouseX = var.left + var.yellowX
        if(var.mouseY > uiMetrics.canvasHeight - var.yellowY):
            var.mouseY = var.bottom - var.yellowY
        if(var.mouseY < var.yellowY):
            var.mouseY = var.top + var.yellowY

        var.left = var.mouseX - var.yellowX
        var.right = var.mouseX + var.yellowX
        var.top = var.mouseY - var.yellowY
        var.bottom = var.mouseY + var.yellowY
        var.resizedImage = (var.image).crop((var.left, var.top, var.right, var.bottom))
        var.resizedImage = (var.resizedImage).resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight), PIL.Image.ANTIALIAS)

        var.imgg = ImageTk.PhotoImage(var.resizedImage)
        canvas.imageID = canvas.create_image(0, 0, image=var.imgg, anchor='nw')
    else:
        var.imgg = ImageTk.PhotoImage(var.resizedImage)
        canvas.imageID = canvas.create_image(0, 0, image=var.imgg, anchor='nw')


def startTurn(uiElements,var,ships,gameRules,uiMetrics):
    print("New Round")
    var.turnInProgress = True
    uiElements.timeElapsedProgressBar['value'] = 0
    for ship1 in var.ships:
        ship1.shotsNotTaken = 0
        ship1.shotsTaken = 0
    for object in uiElements.UIElementsList:
        object.config(state=DISABLED, background="#D0D0D0")
    for object in uiElements.RadioElementsList:
        object.config(state=DISABLED)
    for object in uiElements.uiSystems:
        object.config(state = DISABLED, background="#D0D0D0")


def endTurn(uiElements,var,gameRules,uiMetrics,canvas,ammunitionType,uiIcons): 
    var.turnInProgress = FALSE
    for object in uiElements.UIElementsList:
        object.config(state = NORMAL, bg="#4582ec",highlightcolor = "white",fg = "white",highlightbackground = "#bfbfbf")
    for object in uiElements.RadioElementsList:
        object.config(state = NORMAL)
    for object in uiElements.uiSystems:
        object.config(state = NORMAL, bg="#4582ec",highlightcolor = "white")
    uiElements.gameSpeedScale.config(bg="#4582ec",highlightcolor = "white",fg = "white")
    for ship in var.ships:
        ship.ghostPoints = []
    for ship1 in var.ships:
        if(ship1.owner == "ai1"):
            aiController.moveOrderChoice(ship1,var.ships,var,gameRules,uiMetrics)

            aiController.systemChoice(ship1,var.ships)
        getOrders(ship1,var,gameRules,uiMetrics,True)
    var.updateTimer = 3
    newWindow(uiMetrics,var,canvas)
    detectionCheck(var,uiMetrics)
    drawShips(canvas,var,uiMetrics)
    drawGhostPoints(canvas,var)
    drawSignatures(canvas,var)
    drawLandmarks(var,canvas,uiIcons)
    drawLasers(var,canvas,uiMetrics)
    drawRockets(var,ammunitionType,canvas)
    updateShields(var.ships,var)


def updateScales(uiElements,var,shipLookup):
 #   uiElements.playerAPProgressBar['value'] = shipLookup[0].ap
 #   uiElements.playerAPProgressBar2['value'] = shipLookup[1].ap
 #   uiElements.playerAPProgressBar3['value'] = shipLookup[2].ap
 #   uiElements.enemyAPProgressBar['value'] = shipLookup[3].ap
 #   uiElements.enemyAPProgressBar2['value'] = shipLookup[4].ap
 #   uiElements.enemyAPProgressBar3['value'] = shipLookup[5].ap
 #   uiElements.playerHPProgressBar['value'] = shipLookup[0].hp
 #   uiElements.playerHPProgressBar2['value'] = shipLookup[1].hp
 #   uiElements.playerHPProgressBar3['value'] = shipLookup[2].hp
 #   uiElements.enemyHPProgressBar['value'] = shipLookup[3].hp
 #   uiElements.enemyHPProgressBar2['value'] = shipLookup[4].hp
 #   uiElements.enemyHPProgressBar3['value'] = shipLookup[5].hp

    var.tmpCounter += 1
    shipChosen = shipLookup[var.shipChoice]

    uiElements.timeElapsedProgressBar.config(maximum=var.turnLength)

    i = 0 
    for system in uiElements.uiSystemsProgressbars:
        if(i>=len(shipChosen.systemSlots)):
            break
        (shipChosen.systemSlots[i]).energy = (uiElements.uiSystems[i]).get()
        system1 = shipChosen.systemSlots[i]
        system['value'] = (system1.maxCooldown-system1.cooldown)
        cldwn = round((abs(system1.maxCooldown-system1.cooldown)/float(system1.maxCooldown))*100.0)
        if(cldwn == 100):
            system.config(bootstyle = 'success')
        elif(cldwn < 30):
            system.config(bootstyle = 'danger')
        elif(cldwn > 70):
            system.config(bootstyle = 'primary')
        else:
            system.config(bootstyle = 'warning')
        i+=1

def updateCooldowns(ships,var,shipLookup,uiMetrics):
    for ship in ships:
        for system in ship.systemSlots:
            #change if needed
            energyTicks = system.energy
            while(system.cooldown > 0 and energyTicks):
                system.cooldown -= 1
                energyTicks -= 1
                system.trigger(var,ship,ships,shipLookup,uiMetrics)

def updateEnergy(var,uiElements,shipLookup):
    shipChosen = shipLookup[var.shipChoice]
    tmpEnergy = shipChosen.tmpEnergyLimit
    for system in shipChosen.systemSlots:
        tmpEnergy -= system.energy
    shipChosen.energy = tmpEnergy
    if(tmpEnergy<0):
        (var.uiEnergyLabel).config(foreground = "red")
        for radio in var.shipChoiceRadioButtons:
            radio.configure(state=DISABLED)
            (uiElements.startTurnButton).config(state = DISABLED)
    else:
        (var.uiEnergyLabel).config(foreground = "white")
        for radio in var.shipChoiceRadioButtons:
            radio.configure(state = NORMAL)
            if(not var.turnInProgress):
                (uiElements.startTurnButton).config(state = NORMAL)
    (var.uiEnergyLabel).config(text = "Energy left: " + str(shipChosen.energy))
    

def updateShields(ship1,var):
    for ship1 in var.ships:
        for tmp, progressBar in enumerate(ship1.shieldsLabel):
            if(var.turnInProgress):
                tmpShieldRegen = var.shieldRegen
                while(ship1.shieldsState[tmp] < var.shieldMaxState and tmpShieldRegen > 0):
                    ship1.shieldsState[tmp] += 1
                    tmpShieldRegen -= 1
                    if(ship1.shieldsState[tmp] == var.shieldMaxState):
                        ship1.shields += 1
            if(ship1.shieldsState[tmp] > var.shieldMaxState-var.turnLength):
                progressBar.config(bootstyle = 'primary')
            else:
                progressBar.config(bootstyle = 'danger')

            progressBar['value'] = ship1.shieldsState[tmp] * 100 \
                / var.shieldMaxState
########################################## MULTIPURPOSE #########################################


def radioBox(shipLookup,uiElements,var,uiMetrics,root,canvas):
    var.selection = int((var.radio).get())
    if(var.selection == 0):
        var.shipChoice = shipLookup[0].id
    if(var.selection == 1):
        var.shipChoice = shipLookup[1].id
    if(var.selection == 2):
        var.shipChoice = shipLookup[2].id
    updateBattleUi(shipLookup,uiMetrics,var,root,uiElements,canvas)


def updateLabels(uiElements,shipLookup,var):
    i = shipCounter = 0
    targetLabels = [uiElements.playerLabels,uiElements.playerLabels2,uiElements.playerLabels3, uiElements.enemyLabels,uiElements.enemyLabels2,uiElements.enemyLabels3]
    for label in targetLabels:
        if(shipCounter == var.shipChoice):
            uiElements.systemLFs[shipCounter].config(style = 'Green.TLabelframe')
        else:
            uiElements.systemLFs[shipCounter].config(style = 'Grey.TLabelframe')
            
        label[0].config(text = "Hull: " )
        label[1].config(text = str(shipLookup[shipCounter].hp))
        label[2].config(text = "Armor: " )
        label[3].config(text = str(shipLookup[shipCounter].ap)) 
        label[4].config(text = "") 

        label[5].config(text = "System: ")
        label[6].config(text = "Readiness: ")
        label[7].config(text = "Integrity: ")
        label[8].config(text = "Heat: ")
        label[9].config(text = "Energy: ")

        j = 10

        while(i<len(shipLookup[shipCounter].systemSlots)):
            system = shipLookup[shipCounter].systemSlots[i]
            label[j].config(text = system.name)
            readiness = round((abs(system.maxCooldown-system.cooldown)/float(system.maxCooldown))*100.0)
            if(readiness == 100):
                label[j+1].config(style = "Green.TLabel")
            elif(readiness < 30):
                label[j+1].config(style = "Red.TLabel")
            elif(readiness > 70):
                label[j+1].config(style = "Blue.TLabel")
            else:
                label[j+1].config(style = "Yellow.TLabel")
            label[j+1].config(text = str(readiness))
            integrity = system.integrity
            if(integrity == 100):
                label[j+2].config(style = "Green.TLabel")
            elif(integrity < 30):
                label[j+2].config(style = "Red.TLabel")
            elif(integrity > 70):
                label[j+2].config(style = "Blue.TLabel")
            else:
                label[j+2].config(style = "Yellow.TLabel")
            label[j+2].config(text = str(integrity))
            label[j+3].config(text = str(system.heat))
            label[j+4].config(text = str(system.energy))
            label[j+2].config(anchor = E)
            label[j+3].config(anchor = E)
            label[j+4].config(anchor = E)
            i += 1
            j += 5
        j = 10
        i = 0
        shipCounter += 1


def clearUtilityChoice(uiElements,var):
    for widget in (uiElements.systemsLF).winfo_children():
        widget.destroy()
    (uiElements.systemsLF).destroy()
    uiElements.uiSystems = []
    uiElements.uiSystemsProgressbars = []


def updateBattleUi(shipLookup,uiMetrics,var,root,uiElements,canvas):
    clearUtilityChoice(uiElements,var)
    shipChosen = shipLookup[var.shipChoice]
    uiElements.systemsLF = ttk.Labelframe(root,style = 'Grey.TLabelframe', width=uiMetrics.canvasWidth*4/5, \
                                                    height = uiMetrics.systemScalesLFHeight, text= shipChosen.name + " systems", \
                                                    borderwidth=2, relief="groove")

    var.uiEnergyLabel = ttk.Label(uiElements.systemsLF,style = 'Grey.TLabel', width=20, text = "Energy remaining: " + str(shipChosen.energy), font = "16")
    hideBattleUi(uiElements.staticUi,uiElements)
    placeBattleUi(uiElements,uiMetrics,canvas,var,shipLookup)
        
def mouseOnCanvas(var,uiMetrics):
    if(var.pointerX > uiMetrics.canvasX and var.pointerX <
       (uiMetrics.canvasX + uiMetrics.canvasWidth) and var.pointerY >
            uiMetrics.canvasY and var.pointerY < (uiMetrics.canvasY + uiMetrics.canvasHeight)):
        return True
    else:
        return False

def declareShips(var,config):
        var.playerName = (config.get("Ships", "playerName"))
        var.playerName2 = (config.get("Ships", "playerName2"))
        var.playerName3 = (config.get("Ships", "playerName3"))

        var.enemyName =  (config.get("Ships", "enemyName"))
        var.enemyName2 = (config.get("Ships", "enemyName2"))
        var.enemyName3 = (config.get("Ships", "enemyName3"))
        var.player = 0
        var.player2 = 0
        var.player3 = 0
        var.enemy = 0
        var.enemy2 = 0
        var.enemy3 = 0

        creationList = [var.player, var.player2,var.player3,var.enemy,var.enemy2,var.enemy3]
        nameList = [var.playerName, var.playerName2, var.playerName3, var.enemyName, var.enemyName2, var.enemyName3]
        configList = ["Player", "Player2", "Player3", "Enemy", "Enemy2", "Enemy3"]
        i=0
        for element in creationList:
            targetShipName = nameList[i]
            if(i<=2):               #change if more ships
                owner1 = "player1"
            else:
                owner1 = "ai1"
            creationList[i] = ship(var, 
                    owner=owner1,
                    name=targetShipName, 
                    maxShields = int((config.get(configList[i], "maxShields"))),
                    shields=int((config.get(configList[i], "shields"))), 
                    xPos=int((config.get(configList[i], "xPos"))), 
                    yPos=int((config.get(configList[i], "yPos"))),
                    systemSlots=((config.get(configList[i], "systemSlots1")),
                        config.get(configList[i], "systemSlots2"),
                        config.get(configList[i], "systemSlots3"),
                        config.get(configList[i], "systemSlots4"), 
                        config.get(configList[i], "systemSlots5"),
                        config.get(configList[i], "systemSlots6"),
                        config.get(configList[i], "systemSlots7"),
                        config.get(configList[i], "systemSlots8")),
                    systemStatus=((config.get(configList[i], "systemStatus1")),
                    (config.get(configList[i], "systemStatus2")),
                    (config.get(configList[i], "systemStatus3")),
                    (config.get(configList[i], "systemStatus4")), 
                    (config.get(configList[i], "systemStatus5")),
                    (config.get(configList[i], "systemStatus6")),
                    (config.get(configList[i], "systemStatus7")),
                    (config.get(configList[i], "systemStatus8"))),
                    speed = config.get(configList[i], "speed"), 
                    ghostPoints = [],
                    signatures = [],
                    detectionRange=int(config.get(configList[i], "detectionRange")), 
                    turnRate = float(config.get(configList[i], "turnRate")),
                    maxSpeed = config.get(configList[i], "maxSpeed"),
                    outlineColor = ((config.get(configList[i], "outlineColor"))),
                    id = int((config.get(configList[i], "id"))),
                    hp = int((config.get(configList[i], "hp"))), 
                    ap = int((config.get(configList[i], "ap"))))
            i+=1

        var.player = creationList[0]
        var.player2 = creationList[1]
        var.player3 = creationList[2]
        var.enemy = creationList[3]
        var.enemy2 = creationList[4]
        var.enemy3 = creationList[5]
        (var.ships).append(var.player)
        (var.ships).append(var.player2)
        (var.ships).append(var.player3)

        (var.ships).append(var.enemy)
        (var.ships).append(var.enemy2)
        (var.ships).append(var.enemy3)

############################################ INPUTS #############################################

def bindInputs(root,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType):
    root.bind('<Motion>', lambda e: motion(e, var,root))
    root.bind('<Button-1>', lambda e: mouseButton1(e, var))
    root.bind('<Button-2>', lambda e: mouseButton3(e, var))
    root.bind('<ButtonRelease-2>', lambda e: mouseButton3up(e, var))
    root.bind('<MouseWheel>', lambda e: mouseWheel(e, var,uiMetrics))
    root.bind('<Configure>', lambda e: dragging(e,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root))


def motion(event,var,root):
    var.pointerX = root.winfo_pointerx() - root.winfo_rootx()
    var.pointerY = root.winfo_pointery() - root.winfo_rooty()


def mouseButton1(event, var):  # get left mouse button and set it in var
    if event:
        var.mouseButton1 = True
        var.updateTimer = 2
    else:
        var.mouseButton1 = False


def mouseWheel(event, var,uiMetrics):
    if event.delta > 0:
        var.mouseWheelUp = True
        if(var.zoom < 4 and mouseOnCanvas(var,uiMetrics)):
            var.zoom += 0.2
            var.zoomChange = True
    else:
        if(var.zoom > 1 and mouseOnCanvas(var,uiMetrics)):
            var.zoom -= 0.2
            var.zoomChange = True
        var.mouseWheelDown = True

def mouseButton3(event, var):
    if event:
        var.mouseButton3 = True

def mouseButton3up(event, var):
    if event:
        var.mouseButton3 = False


def dragging(event,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root):
    if event.widget is root:
        if not var.drag == '':
            root.after_cancel(var.drag)
        var.drag = root.after(100, partial(stop_drag,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root))


def stop_drag(var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root):
    var.drag = ''
    root.after(1, partial(update,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType,root))



def trackMouse(var):
    var.pointerDeltaX = var.pointerX - var.prevPointerX
    var.pointerDeltaY = var.pointerY - var.prevPointerY

    var.prevPointerX = var.pointerX
    var.prevPointerY = var.pointerY


######################################################### MAIN ####################################

def saveCurrentGame(var):   
    config = configparser.ConfigParser()
    cwd = Path(sys.argv[0])
    cwd = str(cwd.parent)
    filePath = os.path.join(cwd, "gameData","currentGame.ini")
    config.read(filePath)

    creationList = [var.player, var.player2,var.player3,var.enemy,var.enemy2,var.enemy3]
    #nameList = [var.playerName, var.playerName2, var.playerName3, var.enemyName, var.enemyName2, var.enemyName3]
    configList = ["Player", "Player2", "Player3", "Enemy", "Enemy2", "Enemy3"]
    i=0
    for element in creationList:
        if(not config.has_section(configList[i])):
            config.add_section(configList[i])
        config.set(configList[i], "owner",element.owner)
        config.set(configList[i],"name",element.name)
        config.set(configList[i], "maxShields",str(element.maxShields)),
        config.set(configList[i], "shields",str(element.shields)), 
        config.set(configList[i], "xPos",str(element.xPos)), 
        config.set(configList[i], "yPos",str(element.yPos)),
        j=0
        for system in element.systemSlots:
            config.set(configList[i], ("systemSlots" + str(j+1)),element.systemSlots[j].name)
            config.set(configList[i], ("systemStatus" + str(j+1)),str((element.systemSlots[j]).cooldown))
            j+=1
        config.set(configList[i], "speed",str(element.speed)), 
        config.set(configList[i], "detectionRange",str(element.detectionRange)), 
        config.set(configList[i], "turnRate",str(element.turnRate)),
        config.set(configList[i], "maxSpeed",str(element.maxSpeed)),
        config.set(configList[i], "outlineColor",element.outlineColor),
        config.set(configList[i], "hp",str(element.hp)), 
        config.set(configList[i], "id",str(element.id)),
        config.set(configList[i], "ap",str(element.ap))
        i+=1

    hd = open(filePath, "w")
    config.write(hd)
    hd.close()
        #### wip
def run(config,root,menuUiElements):
    if(naglowek.combatUiReady):
        cinfo = naglowek.combatSystemInfo
        naglowek.combatUiReady = False
        for element in ((naglowek.combatSystemInfo).canvas).imageList :
            del element
        del (naglowek.combatSystemInfo).canvas                # theoretically not necessary but avoids accidental memory leaks
        del (naglowek.combatSystemInfo).uiMetrics             # or carrying over data from previous games
        for element in ((naglowek.combatSystemInfo).uiElements).staticUi:
            element.destroy()
        for element in (cinfo.var).playerShields:
            element.destroy()
        for element in (cinfo.var).playerShields2:
            element.destroy()
        for element in (cinfo.var).playerShields3:
            element.destroy()
        for element in (cinfo.var).enemyShields:
            element.destroy()
        for element in (cinfo.var).enemyShields2:
            element.destroy()
        for element in (cinfo.var).enemyShields3:
            element.destroy()
        for widget in ((cinfo.uiElements).systemsLF).winfo_children():
            widget.destroy()
        for element in ((cinfo.var).shipChoiceRadioButtons):
            element.destroy()
        (cinfo.uiElements).playerSPLF.destroy()
        (cinfo.uiElements).playerSPLF2.destroy()
        (cinfo.uiElements).playerSPLF3.destroy()
        (cinfo.uiElements).enemySPLF.destroy()
        (cinfo.uiElements).enemySPLF2.destroy()
        (cinfo.uiElements).enemySPLF3.destroy()
        for element in ((cinfo.uiElements).UIElementsList):
            element.destroy()
        del (cinfo.var).img
        del (cinfo.var).radio
        ((cinfo.uiElements).playerAPLF)
        (cinfo.uiElements).uiSystems = []
        (cinfo.uiElements).uiSystemsProgressbars = []
        del (cinfo.var)
        del (cinfo.gameRules)
        del (cinfo.ammunitionType)
        del (cinfo.uiIcons)
        del (cinfo.shipLookup)
        del (cinfo.events)
        del (cinfo.uiElements)
        del (cinfo.uiElementsToPlace)

    resume(config,root,menuUiElements)
# main
def resume(config,root,menuUiElements):
    if(not naglowek.combatUiReady):
        cwd = Path(sys.argv[0])
        cwd = str(cwd.parent)
        """
        rootX = root.winfo_screenwidth()
        rootY = root.winfo_screenheight()
        root.attributes('-fullscreen', True)
        """
        #root.deiconify()
        uiMetrics = naglowek.uiMetrics
        var = naglowek.global_var(config,root)
        gameRules = naglowek.game_rules()
        ammunitionType = ammunition_type()
        uiIcons = ui_icons()
        shipLookup = dict
        events = _events()
        uiElements = naglowek.dynamic_object()
        uiElements.systemsLF = ttk.Labelframe(root,style = 'Grey.TLabelframe', text= "" + " systems",borderwidth=2, width=uiMetrics.canvasWidth*4/5)
        uiElements.uiEnergyLabel =  ttk.Label(uiElements.systemsLF,style = 'Grey.TLabel', width=20, text = "Energy remaining: ", font = "16")
        uiElements.staticUi = []
        uiIcons.armorIcon = PhotoImage(file=os.path.join(cwd, "icons","armor.png"))

        # canvas
        var.image = PIL.Image.open(os.path.join(cwd, config.get("Images", "img")))
        var.imageMask = PIL.Image.open(os.path.join(cwd, config.get("Images", "imageMask")))
        var.w,var.h = (var.image).size
        scaleX = var.w / uiMetrics.canvasWidth
        scaleY = var.h / uiMetrics.canvasHeight
        imgRatio = int(var.w/var.h)
        if(scaleX > scaleY):
            uiMetrics.canvasWidth = int(var.w/scaleX)
            uiMetrics.canvasHeight = int((var.h/scaleX))

            var.image = var.image.resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight))
            var.imageMask = var.imageMask.resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight))
        else:
            uiMetrics.canvasWidth = int(var.w/scaleY)
            uiMetrics.canvasHeight = int(var.h/scaleY)
            var.image = var.image.resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight))
            var.imageMask = var.imageMask.resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight))
      #  var.img = var.img.resize((uiMetrics.canvasWidth, uiMetrics.canvasHeight))
        canvas = Canvas(root, width=uiMetrics.canvasWidth, height=uiMetrics.canvasHeight,border=1, relief="groove")
        canvas.ovalList = []
        canvas.availableOvalList = []
        tmp = uiIcons.armorIcon 
        canvas.imageID = canvas.create_image(0,0,image = tmp)
        getZoomMetrics(var,uiMetrics)
        (uiElements.staticUi).append(canvas)
        declareShips(var,config)
        uiElements.rootTitle = (config.get("Root", "title"))
        root.title(uiElements.rootTitle)

        # Ships
        shipLookup = {
        0: var.player,
        1: var.player2,
        2: var.player3,
        3: var.enemy,
        4: var.enemy2,
        5: var.enemy3
        }

    #    land1 = landmark(200, 200, 3200, 3200, 50, 'armor')
    #    (var.landmarks).append(land1)

        
        var.resizedImage = var.image
        canvas.imageList = []
        canvas.elements = []
        newWindow(uiMetrics,var,canvas)
        # item with background to avoid python bug people were mentioning about disappearing non-anchored images


        canvas.imageList.append(var.image)
        canvas.imageList.append(var.imageMask)
        canvas.imageList.append(var.resizedImage)

        var.mask = createMask(var,uiMetrics)


        uiElements.UIElementsList = []
        uiElements.RadioElementsList = []

        uiElements.gameSpeedScale = tk.Scale(root, orient=HORIZONTAL, length=100, from_=1, to=16)
        uiElements.gameSpeedL = ttk.Label(root, style = 'Grey.TLabel', text = "Playback Speed:")
        var.img = tk.PhotoImage(file= os.path.join(cwd, config.get("Images", "img")))
        (uiElements.gameSpeedScale).set(3)
        uiElements.timeElapsedLabel = ttk.Label(root, style = 'Grey.TLabel', text="Time elapsed")
        uiElements.timeElapsedProgressBar = ttk.Progressbar(root, maximum=var.turnLength, variable=1,  orient='horizontal',
                                                mode='determinate', length=uiMetrics.shipDataWidth)

        uiElements.startTurnButton = tk.Button(root, text="Start turn", command=lambda:[startTurn(uiElements,var,var.ships,gameRules,uiMetrics)], width = 20, height= 7)
        uiElements.exitButton = tk.Button(root, text="Exit", command=exit)
        uiElements.exitToMenuButton = tk.Button(root, text="Exit to menu", command=lambda:[placeMenuUi(root,menuUiElements,uiMetrics), hideBattleUi(uiElements.staticUi,uiElements), finishSetTrue(var),saveCurrentGame(var)], width = 20, height= 7)

        (uiElements.staticUi).append(uiElements.gameSpeedScale)
        (uiElements.staticUi).append(uiElements.gameSpeedL)
        (uiElements.staticUi).append(uiElements.timeElapsedLabel)
        (uiElements.staticUi).append(uiElements.timeElapsedProgressBar)
        (uiElements.staticUi).append(uiElements.startTurnButton)
        (uiElements.staticUi).append(uiElements.exitButton)
        (uiElements.staticUi).append(uiElements.exitToMenuButton)

        for ship1 in var.ships:
            if(ship1.owner == "player1"):
                putTracer(ship1,var,gameRules,uiMetrics)

        # ship shields
        uiElements.playerSPLF = ttk.Labelframe(root, style = 'Grey.TLabelframe', text= var.playerName + " Shields",
                                            borderwidth=2, relief="groove")
        uiElements.playerSPLF2 = ttk.Labelframe(root,style = 'Grey.TLabelframe',  text= var.playerName2 + " Shields",
                                            borderwidth=2, relief="groove")
        uiElements.playerSPLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text= var.playerName3 + " Shields",
                                            borderwidth=2, relief="groove")
        uiElements.enemySPLF = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.enemyName + " Shields",
                                        borderwidth=2, relief="groove")
        uiElements.enemySPLF2 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.enemyName2 + " Shields",
                                            borderwidth=2, relief="groove")
        uiElements.enemySPLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text= var.enemyName3 + " Shields",
                                            borderwidth=2, relief="groove")
        
        uiElements.enemyLF = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[3].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        uiElements.enemyLF2 = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[4].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        uiElements.enemyLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[5].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        uiElements.playerLF = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[0].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        uiElements.playerLF2 = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[1].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        uiElements.playerLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe',text = shipLookup[2].name, height = uiMetrics.canvasHeight/5*2, width = uiMetrics.systemsLFWidth)
        var.playerShields = []
        var.playerShields2 = []
        var.playerShields3 = []
        var.enemyShields = []
        var.enemyShields2 = []
        var.enemyShields3 = []

        targets = [var.playerShields,var.playerShields2,var.playerShields3,var.enemyShields,var.enemyShields2,var.enemyShields3]
        elements = [var.player,var.player2,var.player3,var.enemy,var.enemy2,var.enemy3]
        labelframes = [uiElements.enemyLF,uiElements.enemyLF2, uiElements.enemyLF3, uiElements.playerLF, uiElements.playerLF2, uiElements.playerLF3]
        for target,element,labelframe in zip(targets,elements,labelframes):
            x = (element).maxShields
            n = 0
            while(n < x):
                target.append(ttk.Progressbar(
                    labelframe, maximum=100, length=math.floor((uiMetrics.systemScalesLFWidth-10)/x * 4/5), variable=100))
                n += 1
        # ship armor
        uiElements.playerAPLF = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.playerName + " Armor Effectivness",
                                            borderwidth=2, relief="groove")
        uiElements.playerAPProgressBar = ttk.Progressbar(
            uiElements.playerAPLF, maximum=(var.player).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)
        uiElements.playerAPLF2 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.playerName2 + " Armor Effectivness",
                                            borderwidth=2, relief="groove")
        uiElements.playerAPProgressBar2 = ttk.Progressbar(
            uiElements.playerAPLF2, maximum=(var.player2).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)
        uiElements.playerAPLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.playerName3 + " Armor Effectivness",
                                            borderwidth=2, relief="groove")
        uiElements.playerAPProgressBar3 = ttk.Progressbar(
            uiElements.playerAPLF3, maximum=(var.player3).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)
        uiElements.enemyAPLF = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.enemyName + " Armor Effectivness",
                                        borderwidth=2, relief="groove")
        uiElements.enemyAPProgressBar = ttk.Progressbar(
            uiElements.enemyAPLF, maximum=(var.enemy).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)
        uiElements.enemyAPLF2 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text= var.enemyName2 + " Armor Effectivness",
                                            borderwidth=2, relief="groove")
        uiElements.enemyAPProgressBar2 = ttk.Progressbar(
            uiElements.enemyAPLF2, maximum=(var.enemy).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)

        uiElements.enemyAPLF3 = ttk.Labelframe(root, style = 'Grey.TLabelframe', text=var.enemyName3 + " Armor Effectivness",
                                            borderwidth=2, relief="groove")
        uiElements.enemyAPProgressBar3 = ttk.Progressbar(
            uiElements.enemyAPLF3, maximum=(var.enemy).maxAp, length=(uiMetrics.shipDataWidth-10), variable=100)

            
        (uiElements.staticUi).append(uiElements.playerAPLF)
        (uiElements.staticUi).append(uiElements.playerAPLF2)
        (uiElements.staticUi).append(uiElements.playerAPLF3)
        (uiElements.staticUi).append(uiElements.enemyAPLF)
        (uiElements.staticUi).append(uiElements.enemyAPLF2)
        (uiElements.staticUi).append(uiElements.enemyAPLF3)

        for ship1 in var.ships:
            if(ship1.owner == "ai1"):
                aiController.moveOrderChoice(ship1,var.ships,var,gameRules,uiMetrics)

        ######################################################### PROGRESSBAR ASSIGNMENT ####################################

        (var.player).shieldsLabel = var.playerShields
        (var.player2).shieldsLabel = var.playerShields2
        (var.player3).shieldsLabel = var.playerShields3
        (var.enemy).shieldsLabel = var.enemyShields
        (var.enemy2).shieldsLabel = var.enemyShields2
        (var.enemy3).shieldsLabel = var.enemyShields3

        (uiElements.tmpShieldsLabel) = []
        (uiElements.tmpShieldsLabel).append(var.playerShields)
        (uiElements.tmpShieldsLabel).append(var.playerShields2)
        (uiElements.tmpShieldsLabel).append(var.playerShields3)
        (uiElements.tmpShieldsLabel).append(var.enemyShields)
        (uiElements.tmpShieldsLabel).append(var.enemyShields2)
        (uiElements.tmpShieldsLabel).append(var.enemyShields3)        # create list of elements to disable if round is in progress
        (uiElements.UIElementsList).append(uiElements.gameSpeedScale)
        (uiElements.UIElementsList).append(uiElements.startTurnButton)
        (uiElements.UIElementsList).append(uiElements.exitToMenuButton)

      #  (uiElements.staticUi).append(uiElements.systemsLabelFrame)

        uiElementsToPlace = uiElements
        
        (uiElements.staticUi).append(uiElements.playerSPLF)
        (uiElements.staticUi).append(uiElements.playerSPLF2)
        (uiElements.staticUi).append(uiElements.playerSPLF3)
        (uiElements.staticUi).append(uiElements.enemySPLF)
        (uiElements.staticUi).append(uiElements.enemySPLF2)
        (uiElements.staticUi).append(uiElements.enemySPLF3)

        var.shipChoiceRadioButtons = []
        radioCommand = partial(radioBox,shipLookup , uiElements,var,uiMetrics,root,canvas)

##################################

        uiElements.enemyLabels = []
        uiElements.enemyLabels2 = []
        uiElements.enemyLabels3 = []
        uiElements.playerLabels = []
        uiElements.playerLabels2 = []
        uiElements.playerLabels3 = []
        uiElements.systemLFs = []

        targets = [uiElements.playerLabels, uiElements.playerLabels2, uiElements.playerLabels3,uiElements.enemyLabels, uiElements.enemyLabels2, uiElements.enemyLabels3]


        (uiElements.staticUi).append(uiElements.enemyLF)
        (uiElements.staticUi).append(uiElements.enemyLF2)
        (uiElements.staticUi).append(uiElements.enemyLF3)
        (uiElements.staticUi).append(uiElements.playerLF)
        (uiElements.staticUi).append(uiElements.playerLF2)
        (uiElements.staticUi).append(uiElements.playerLF3)

        targetLFs = [uiElements.playerLF,uiElements.playerLF2,uiElements.playerLF3,uiElements.enemyLF,uiElements.enemyLF2,uiElements.enemyLF3]
        shipID = 0
        for target,targetLF in zip(targets,targetLFs):
            i = 0
            system = shipLookup[shipID].systemSlots[i] 
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Hull: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(shipLookup[3].hp)))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Armor: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(shipLookup[3].ap)))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = ""))

            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "System: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Readiness: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Integrity: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Heat: "))
            target.append(ttk.Label(targetLF, style='Grey.TLabel', text = "Energy: "))
            for element in shipLookup[shipID].systemSlots:
                system = shipLookup[shipID].systemSlots[i]
                target.append(ttk.Label(targetLF, style='Grey.TLabel', text = system.name))
                target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(round((system.cooldown/system.maxCooldown))*100)))
                target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(system.integrity)))
                target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(system.heat)))
                target.append(ttk.Label(targetLF, style='Grey.TLabel', text = str(system.energy)))
                (uiElements.staticUi).append(target[i])
                i+=1
            shipID += 1

        uiElements.systemLFs.append(uiElements.playerLF)
        uiElements.systemLFs.append(uiElements.playerLF2)
        uiElements.systemLFs.append(uiElements.playerLF3)
        uiElements.systemLFs.append(uiElements.enemyLF)
        uiElements.systemLFs.append(uiElements.enemyLF2)
        uiElements.systemLFs.append(uiElements.enemyLF3)

        # ships choice
        var.shipChoice = (var.player).name
        uiElements.shipChoiceRadioButton0 = ttk.Radiobutton(root, style = "Grey.TRadiobutton", text=(var.ships[0]).name, variable=var.radio, value=0, command=radioCommand)
        uiElements.shipChoiceRadioButton1 = ttk.Radiobutton(root, style = "Grey.TRadiobutton", text=(var.ships[1]).name, variable=var.radio, value=1, command=radioCommand)
        uiElements.shipChoiceRadioButton2 = ttk.Radiobutton(root, style = "Grey.TRadiobutton", text=(var.ships[2]).name, variable=var.radio, value=2, command=radioCommand)
        (uiElements.RadioElementsList).append(uiElements.shipChoiceRadioButton0)
        (uiElements.RadioElementsList).append(uiElements.shipChoiceRadioButton1)
        (uiElements.RadioElementsList).append(uiElements.shipChoiceRadioButton2)

        (var.shipChoiceRadioButtons).append(uiElements.shipChoiceRadioButton0)
        (var.shipChoiceRadioButtons).append(uiElements.shipChoiceRadioButton1)
        (var.shipChoiceRadioButtons).append(uiElements.shipChoiceRadioButton2)
        
        (uiElements.staticUi).append(uiElements.shipChoiceRadioButton0)
        (uiElements.staticUi).append(uiElements.shipChoiceRadioButton1)
        (uiElements.staticUi).append(uiElements.shipChoiceRadioButton2)

        radioBox(shipLookup,uiElements,var,uiMetrics,root,canvas)

        bindInputs(root,var,uiElements,uiMetrics,uiIcons,canvas,events,shipLookup,gameRules,ammunitionType)
        
        # first update 
        endTurn(uiElements,var,gameRules,uiMetrics,canvas,ammunitionType,uiIcons)
        

        (naglowek.combatSystemInfo).canvas = canvas
        (naglowek.combatSystemInfo).uiMetrics = uiMetrics
        (naglowek.combatSystemInfo).var = var
        (naglowek.combatSystemInfo).gameRules = gameRules
        (naglowek.combatSystemInfo).ammunitionType = ammunitionType
        (naglowek.combatSystemInfo).uiIcons = uiIcons
        (naglowek.combatSystemInfo).shipLookup = shipLookup
        (naglowek.combatSystemInfo).events = events
        (naglowek.combatSystemInfo).uiElements = uiElements
        (naglowek.combatSystemInfo).canvas = canvas
        (naglowek.combatSystemInfo).uiElementsToPlace = uiElementsToPlace
        naglowek.combatUiReady = True
        # clock       

    else:
        ((naglowek.combatSystemInfo).var).finished = False
        ((naglowek.combatSystemInfo).uiElements).systemsLF = ttk.Labelframe(root,text= "" + " systems",borderwidth=2,style='Grey.TLabelframe.Label')
        updateBattleUi((naglowek.combatSystemInfo).shipLookup,(naglowek.combatSystemInfo).uiMetrics,(naglowek.combatSystemInfo).var,root,(naglowek.combatSystemInfo).uiElements,(naglowek.combatSystemInfo).canvas)
    update((naglowek.combatSystemInfo).var,(naglowek.combatSystemInfo).uiElements,(naglowek.combatSystemInfo).uiMetrics,(naglowek.combatSystemInfo).uiIcons,(naglowek.combatSystemInfo).canvas,(naglowek.combatSystemInfo).events,(naglowek.combatSystemInfo).shipLookup,(naglowek.combatSystemInfo).gameRules,(naglowek.combatSystemInfo).ammunitionType,root)