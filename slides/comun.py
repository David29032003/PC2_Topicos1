import subprocess

from pptx import Presentation
from pptx.util import Inches


def nueva_presentacion():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    return prs


def exportar(pptx, pdf, carpeta_png):
    # pdf y png con PowerPoint; si ya habia presentaciones abiertas no se cierra
    carpeta_png.mkdir(exist_ok=True)
    for viejo in carpeta_png.glob("*.png"):
        viejo.unlink()
    ps = f"""
$app = New-Object -ComObject PowerPoint.Application
$abiertas = $app.Presentations.Count
$p = $app.Presentations.Open('{pptx}', $true, $false, $false)
$p.SaveAs('{pdf}', 32)
$i = 1
foreach ($s in $p.Slides) {{ $s.Export('{carpeta_png}\\slide' + $i + '.png', 'PNG', 1600, 900); $i++ }}
$p.Close()
if ($abiertas -eq 0) {{ $app.Quit() }}
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
