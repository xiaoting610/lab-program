# -*- coding: utf-8 -*-
"""
Created on Fri May 23 09:20:48 2014

@author: Curio
"""

xmlFile = r'D:\brian\zby\zby.20140314.m.a.xml'
saveFile = r'D:\brian\zby\zby.20140314.m.a.AreaNew.xml'

from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.ops import cascaded_union
from scipy.optimize import leastsq
from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Kernel import Point_2
#from CGAL.CGAL_Kernel import Segment_2
from CGAL.CGAL_Kernel import Segment_3
from CGAL.CGAL_Kernel import Polygon_2
from CGAL.CGAL_Kernel import Plane_3
from CGAL.CGAL_Kernel import Line_3
#from CGAL.CGAL_Kernel import Ray_2
from CGAL.CGAL_Kernel import Ray_3
from CGAL.CGAL_Kernel import Vector_3
#from CGAL.CGAL_Kernel import Vector_2
from CGAL.CGAL_Kernel import intersection
from CGAL.CGAL_Kernel import squared_distance
#from CGAL.CGAL_AABB_tree import AABB_tree_Segment_3_soup
from CGAL import CGAL_Convex_hull_2
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import SubElement
import math
import sys
sys.setrecursionlimit(100000000) 

def lineFitFunc(lineDirection, pointStd, pointTest) : 
    newLine = Line_3(pointStd, Vector_3(lineDirection[0], lineDirection[1], lineDirection[2]))
    return [squared_distance(x, newLine) for x in pointTest]
    
def getNodeMapSetCentroids(rootObj, nodeMap) : 
    for subObj in rootObj.findall('t2_node') : 
        zCor = infoMap[subObj.get('lid')]
        centroidPoint = Point(float(subObj.get('x')), float(subObj.get('y')))
        flatRadius = 0
        realFlatRadius = 0
        allPolygons = [];
        for newArea in subObj.findall('t2_area') : 
            for newPath in newArea.findall('t2_path') : 
                pathCorStr = newPath.get('d').split()
                allCors = [float(pathCorStr[i]) for i in range(0, len(pathCorStr)) if i % 3 != 0]
                newPolygon = Polygon([(allCors[i], allCors[i + 1]) for i in range(0, len(allCors), 2)])
                if newPolygon.contains(centroidPoint) : 
                    allPolygons.append(newPolygon)
            subObj.remove(newArea)
        if len(allPolygons) != 0 : 
            finalPolygon = cascaded_union(allPolygons)
            polygonBounds = finalPolygon.bounds
            widLen = polygonBounds[2] - polygonBounds[0]
            heiLen = polygonBounds[3] - polygonBounds[1]
            flatRadius = widLen * widLen + heiLen * heiLen
            pathStr = 'M ' + ' '.join([str(int(x[0])) + ' ' + str(int(x[1])) + ' L' for x in list(finalPolygon.exterior.coords)])
            SubElement(SubElement(subObj, 't2_area'), 't2_path', {'d' : pathStr[: -1] + 'z'})
            centroidPoint1 = finalPolygon.centroid
            if finalPolygon.contains(centroidPoint1) : centroidPoint = centroidPoint1
            realFlatRadius = math.sqrt(finalPolygon.convex_hull.area / math.pi)
        nodeMap.append((subObj.get('oid'), Point_3(float(subObj.get('x')), float(subObj.get('y')), float(zCor)), flatRadius))
        subObj.set('x', str(centroidPoint.x))
        subObj.set('y', str(centroidPoint.y))
        subObj.set('flatradius', str(realFlatRadius * pixelWidth))
        getNodeMapSetCentroids(subObj, nodeMap)
     
        
def getSurfaceInfoAndCentroidnormal(rootObj, SurfaceInfo, centroidNormals, rootCentroid = None, rootPolygon = None) : 
    for subObj in rootObj.findall('t2_node') : 
        pointsTest = []
        zCor = float(infoMap[subObj.get('lid')])
        xCor = float(subObj.get('x'))
        yCor = float(subObj.get('y'))
        currentPoint = Point_3(xCor, yCor, zCor)
        pointsTest.append(currentPoint)
        if rootObj.tag == 't2_node' : 
            pointsTest.append(Point_3(float(rootObj.get('x')), float(rootObj.get('y')), float(infoMap[rootObj.get('lid')])))
        for childNode in subObj.findall('t2_node') : 
            pointsTest.append(Point_3(float(childNode.get('x')), float(childNode.get('y')), float(infoMap[childNode.get('lid')])))
        if len(pointsTest) == 1 : return
        if len(pointsTest) == 2 : pointsTest.append(pointsTest[0])
        finalDirection = leastsq(lineFitFunc, [pointsTest[-2].x() - pointsTest[0].x(), pointsTest[-2].y() - pointsTest[0].y(), pointsTest[-2].z() - pointsTest[0].z()], (pointsTest[0], pointsTest))
        finalNormal = Vector_3(finalDirection[0][0], finalDirection[0][1], finalDirection[0][2])
        if math.isnan(finalNormal.x()) or math.isnan(finalNormal.y()) or math.isnan(finalNormal.z()) or (finalNormal.x() == 0 and finalNormal.y() == 0 and finalNormal.z() == 0):
            finalNormal = Vector_3(pointsTest[-1].x() - pointsTest[0].x(), pointsTest[-1].y() - pointsTest[0].y(), pointsTest[-1].z() - pointsTest[0].z())
        centroidNormals.append((Point_3(xCor, yCor, zCor), finalNormal))
        
        pointList = []
        for newArea in subObj.findall('t2_area') : 
            for newPath in newArea.findall('t2_path') : 
                pathCorStr = newPath.get('d').split()
                allCors = [float(pathCorStr[i]) for i in range(0, len(pathCorStr)) if i % 3 != 0]
                pointList = [Point_3(allCors[i], allCors[i + 1], zCor) for i in range(0, len(allCors), 2)]
#                pointList = [Point_2(allCors[i], allCors[i + 1]) for i in range(0, len(allCors), 2)]
        subPolygon = None
        if pointList : 
            subPolygon = [Segment_3(pointList[i], pointList[i + 1]) for i in range(0, len(pointList) - 1)]
            if rootPolygon : 
#                rootTree = AABB_tree_Segment_3_soup(rootPolygon)
                for newPt in pointList : 
                    newRay = Ray_3(rootCentroid, Vector_3(currentPoint, newPt))
#                    newIntersections = []
#                    rootTree.all_intersections(newRay, newIntersections)
                    newIntersections = [newObj.get_Point_3() for newObj in [intersection(newRay, newSegment) for newSegment in rootPolygon] if (not newObj.empty()) and newObj.is_Point_3()]
#                    newRay = Ray_2(Point_2(rootCentroid.x(), rootCentroid.y()), Vector_2(Point_2(currentPoint.x(), currentPoint.y()), newPt))
#                    newIntersections = [newObj.get_Point_2() for newObj in [intersection(newRay, newSegment) for newSegment in rootPolygon] if (not newObj.empty()) and newObj.is_Point_2()]
                    if len(newIntersections) == 0 : 
                        print 'opps!'
                    SurfaceInfo.extend([Segment_3(newPt, newPoint) for newPoint in newIntersections])
#                    SurfaceInfo.extend([Segment_3(Point_3(newPt.x(), newPt.y(), zCor), Point_3(newPoint.x(), newPoint.y(), rootCentroid.z())) for newPoint in newIntersections])
#            subPolygon = [Segment_2(pointList[i], pointList[i + 1]) for i in range(0, len(pointList)) if i != len(pointList) - 1]
        if subPolygon is not None : 
            SurfaceInfo.extend(subPolygon)
#            SurfaceInfo.extend([Segment_3(Point_3(newSegment.source().x(), newSegment.source().y(), zCor), Point_3(newSegment.target().x(), newSegment.target().y(), zCor)) for newSegment in subPolygon])
            getSurfaceInfoAndCentroidnormal(subObj, SurfaceInfo, centroidNormals, currentPoint, subPolygon)
        else : 
            getSurfaceInfoAndCentroidnormal(subObj, SurfaceInfo, centroidNormals, rootCentroid, rootPolygon)

def findRightNormal(newNode, centroidNormals) :
    minDist = sys.float_info.max
    rightNormal = Vector_3()
    for newCentroid in centroidNormals : 
        newDist = squared_distance(newNode, newCentroid[0])
        if newDist < minDist : 
            minDist = newDist
            rightNormal = newCentroid[1]
    return rightNormal

def setArea(rootObj, areaMap) : 
    for subObj in rootObj.findall('t2_node') : 
        subObj.set('crossradius', areaMap[subObj.get('oid')])
        setArea(subObj, areaMap)

mainRoot = ET.parse(xmlFile).getroot()
layerSet = mainRoot.findall('t2_layer_set')[0]
infoMap = {}
for newLayer in layerSet.findall('t2_layer'):
    infoMap[newLayer.get('oid')] = newLayer.get('z')
    
pixelWidth = float(layerSet.find("t2_calibration").get("pixelWidth"))

for newTree in layerSet.findall('t2_areatree') : 
#    if newTree.get('oid') != '22476' : continue
    print 'processing ' + newTree.get('oid')
    nodeMap = []
    SurfaceInfo = []
    centroidNormals = []
    getNodeMapSetCentroids(newTree, nodeMap)
    getSurfaceInfoAndCentroidnormal(newTree, SurfaceInfo, centroidNormals)
    if len(SurfaceInfo) == 0 : 
        print newTree.get('oid') + ' no surface!'
        continue
    areaMap = {};
    for newNode in nodeMap : 
        planeNormal = findRightNormal(newNode[1], centroidNormals)
        sqLen = math.sqrt(planeNormal.squared_length())
        cosinXY = abs(planeNormal.z()) / sqLen
        cosinXZ = abs(planeNormal.y()) / sqLen
        cosinYZ = abs(planeNormal.x()) / sqLen
        if cosinXY == 0 and cosinXZ == 0 and cosinYZ == 0 : 
            areaMap[newNode[0]] = '0'
            continue
        planeQuery = Plane_3(newNode[1], planeNormal)
        newIntersections = [newObj.get_Point_3() for newObj in [intersection(planeQuery, newSegment) for newSegment in SurfaceInfo] if (not newObj.empty()) and newObj.is_Point_3()]
        if len(newIntersections) == 0 : 
            print 'big opps!'
        allCrossSectionPoints = []
        maxDist = newNode[2] * 1.2
        for newPt in newIntersections : 
            if squared_distance(newPt, newNode[1]) > maxDist : continue
            if cosinXY != 0 : 
                allCrossSectionPoints.append(Point_2(newPt.x(), newPt.y()))
            elif cosinXZ != 0 : 
                allCrossSectionPoints.append(Point_2(newPt.x(), newPt.z()))
            else : 
                allCrossSectionPoints.append(Point_2(newPt.y(), newPt.z()))
        convexPoints = []
        CGAL_Convex_hull_2.convex_hull_2(allCrossSectionPoints, convexPoints)
        AAA = Polygon_2(convexPoints)
        AAA.edges_circulator
        convexArea = abs(Polygon_2(convexPoints).area())
        if cosinXY != 0 : convexArea /= cosinXY
        elif cosinXZ != 0 : convexArea /= cosinXZ
        else : convexArea /= cosinYZ
        areaMap[newNode[0]] = str(int(math.sqrt(convexArea / math.pi) * pixelWidth))
    setArea(newTree, areaMap)
    print newTree.get('oid') + ' Done!'
    
headerStr = ''
mainFileHandle = open(xmlFile)
for newLine in mainFileHandle : 
    if newLine == '<trakem2>\n' : 
        break
    headerStr += newLine
mainFileHandle.close()
treeStr = ET.tostring(mainRoot, 'ISO-8859-1')
outFileHandle = open(saveFile, 'w')
outFileHandle.write(headerStr)
outFileHandle.write(treeStr[treeStr.index('\n') + 1 : ])
outFileHandle.close()