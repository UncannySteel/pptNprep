# QA for the talk deck, using PowerPoint itself.
#
# Opens the deck read-only (PowerPoint refuses or repairs a malformed file, so a
# clean open is the first check), lists each slide's animation count, flags any
# text that overflows its box, and exports every slide twice: as it looks before
# the first click ("start") and after the last ("end").
#
#   powershell -ExecutionPolicy Bypass -File tools/deck/qa_render.ps1 [deck.pptx] [out dir]

param(
    [string]$Deck = (Join-Path $PSScriptRoot "..\..\ABOT-R10HTC-2026-talk.pptx"),
    [string]$OutDir = (Join-Path $env:TEMP "abot-deck-qa")
)
$Deck = (Resolve-Path $Deck).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter "*.png" | Remove-Item -Force

function Test-Overflow($shape, $slideNo) {
    if ($shape.Type -eq 6) {
        foreach ($child in $shape.GroupItems) { Test-Overflow $child $slideNo }
        return
    }
    if (-not $shape.HasTextFrame) { return }
    $tf = $shape.TextFrame2
    if (-not $tf.HasText) { return }
    $tr = $tf.TextRange
    $innerH = $shape.Height - $tf.MarginTop - $tf.MarginBottom
    $innerW = $shape.Width - $tf.MarginLeft - $tf.MarginRight
    $over = $tr.BoundHeight - $innerH
    $wide = $tr.BoundWidth - $innerW
    if ($over -gt 1.5 -or $wide -gt 1.5) {
        $t = ($tr.Text -replace "[`r`n`v]", " / ")
        if ($t.Length -gt 60) { $t = $t.Substring(0, 60) + "..." }
        "  OVERFLOW slide {0}: '{1}' height +{2:N1}pt width +{3:N1}pt  [{4}]" -f $slideNo, $shape.Name, $over, $wide, $t
    }
}

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Deck, $true, $false, $false)
"Opened {0}: {1} slides" -f (Split-Path $Deck -Leaf), $pres.Slides.Count
foreach ($slide in $pres.Slides) {
    $i = $slide.SlideIndex
    $seq = $slide.TimeLine.MainSequence
    $clicks = 0
    $first = @{}; $last = @{}
    foreach ($e in $seq) {
        if ($e.Timing.TriggerType -eq 1) { $clicks++ }
        $name = $e.Shape.Name + "#" + $e.Shape.Id
        $kind = if ($e.Exit) { "exit" } elseif ($e.EffectType -in 6, 8, 59, 61) { "emph" } else { "entr" }
        if ($kind -ne "emph") {
            if (-not $first.ContainsKey($name)) { $first[$name] = @($e.Shape, $kind) }
            $last[$name] = @($e.Shape, $kind)
        }
    }
    "slide {0}: {1} effects, {2} clicks, notes {3} chars" -f $i, $seq.Count, $clicks, $slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text.Length
    foreach ($sh in $slide.Shapes) { Test-Overflow $sh $i }

    # start state: hide whatever first enters; end state: hide whatever last exits
    foreach ($v in $first.Values) { if ($v[1] -eq "entr") { $v[0].Visible = 0 } }
    $slide.Export((Join-Path $OutDir ("s{0:D2}-start.png" -f $i)), "PNG", 1600, 900)
    foreach ($v in $first.Values) { $v[0].Visible = -1 }
    foreach ($v in $last.Values) { if ($v[1] -eq "exit") { $v[0].Visible = 0 } }
    $slide.Export((Join-Path $OutDir ("s{0:D2}-end.png" -f $i)), "PNG", 1600, 900)
    foreach ($v in $last.Values) { $v[0].Visible = -1 }
}
$pres.Close()
$app.Quit()
"Images in $OutDir"
