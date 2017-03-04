import math

def candMedian(dataPoints):
    #Calculate the first candidate median as the geometric mean
    tempX = 0.0
    tempY = 0.0
    
    for i in range(0,len(dataPoints)):
        tempX += dataPoints[i][0]
        tempY += dataPoints[i][1]
    
    return [tempX/len(dataPoints),tempY/len(dataPoints)]

def numersum(testMedian,dataPoint):
    # Provides the denominator of the weiszfeld algorithm depending on whether you are adjusting the candidate x or y
    return 1/math.sqrt((testMedian[0]-dataPoint[0])**2 + (testMedian[1]-dataPoint[1])**2)

def denomsum(testMedian, dataPoints):
    # Provides the denominator of the weiszfeld algorithm
    temp = 0.0
    for i in range(0,len(dataPoints)):
        temp += 1/math.sqrt((testMedian[0] - dataPoints[i][0])**2 + (testMedian[1] - dataPoints[i][1])**2)
    return temp

def objfunc(testMedian, dataPoints):
    # This function calculates the sum of linear distances from the current candidate median to all points
    # in the data set, as such it is the objective function we are minimising.
    temp = 0.0
    for i in range(0,len(dataPoints)):
        temp += math.sqrt((testMedian[0]-dataPoints[i][0])**2 + (testMedian[1]-dataPoints[i][1])**2)
    return temp

def getMed(dataPoints):

    testMedian = candMedian(dataPoints)

    # numIter depends on how long it take to get a suitable convergence of objFunc
    numIter = 25

    #minimise the objective function.
    for x in range(0,numIter):

        denom = denomsum(testMedian,dataPoints)
        nextx = 0.0
        nexty = 0.0

        for y in range(0,len(dataPoints)):
            nextx += (dataPoints[y][0] * numersum(testMedian,dataPoints[y]))/denom
            nexty += (dataPoints[y][1] * numersum(testMedian,dataPoints[y]))/denom

        testMedian = [nextx,nexty]
    return(testMedian)
