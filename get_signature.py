import aiohttp, asyncio
import json
from PIL import Image, ImageDraw, ImageFilter


def DrawSignature_IMG(listLines, nWidth, nHeight, nLineWidth = 4):
    img = Image.new("RGB", (nWidth, nHeight), color = (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i, listLine in enumerate(listLines):
        for j, listPoint in enumerate(listLine):
            listLines[i][j] = (int(listPoint[0]), int(listPoint[1]),)
        draw.line(listLines[i], fill = (0, 0, 0), width = nLineWidth, joint = 'curve')
    blurred_image = img.filter(ImageFilter.BoxBlur(1))
    #img.show()
    return blurred_image


def DrawSignature_GIF(listLines, nWidth, nHeight, nLineWidth = 4):
    img = Image.new("RGB", (nWidth, nHeight), color = (255, 255, 255))
    draw = ImageDraw.Draw(img)
    listImages = [img]
    for i, listLine in enumerate(listLines):
        for j, listPoint in enumerate(listLine):
            listLines[i][j] = (int(listPoint[0]), int(listPoint[1]),)
        draw.line(listLines[i], fill = (0, 0, 0), width = nLineWidth, joint = 'curve')
        listImages.append(img.copy().filter(ImageFilter.BoxBlur(1)))
    blurred_image = img.filter(ImageFilter.BoxBlur(1))
    return blurred_image, listImages


##sSurname, sName, sMiddle, nWidth, nHeight, nEffectId
async def GetSignature(sSurname, sName, sMiddle, nWidth = 1024, nHeight = 1024, nEffectId = 1, nLineWidth = 4, sFormat = 'JPEG'):
    dictParams =  {'surname' : sSurname ,
                   'name'    : sName    ,
                   'middle'  : sMiddle  ,
                   'width'   : nWidth   ,
                   'height'  : nHeight  ,
                   'effect'  : nEffectId}

    async with aiohttp.ClientSession('http://localhost') as session:
        async with session.post('/podpis-online_bot/get_signature.php',  params = dictParams) as resp:
            # resp.status
            sRespText = (await (resp.text()))
            try:
                listRespPoints = json.loads(sRespText)
            except:
                print('Error in GetSignature')
                print(dictParams)
                listRespPoints = list()

            if listRespPoints:
                if sFormat == 'JPEG':
                    return DrawSignature_IMG(listRespPoints[0], nWidth, nHeight, nLineWidth = nLineWidth)
                elif sFormat == 'GIF':
                    return DrawSignature_GIF(listRespPoints[0], nWidth, nHeight, nLineWidth = nLineWidth)
