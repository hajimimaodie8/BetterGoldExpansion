# [bgn10-perturb] 扰动实测脚本（1.7 bg-n10 轮1 后半 + 轮2）
# 跑法：pwsh -File docs\bgn10-证据\脚本副本\bgn10_perturb.ps1
# 每个用例：改 → 跑关卡 → 记录 exit → **逐字节复原** → SHA256 自证。
$ErrorActionPreference = "Stop"
$repo = "E:\mc\mcmod\bettergold-template-1.21.1"
Set-Location $repo
$ev = "docs\bgn10-证据"
$log = @()
$env:PYTHONIOENCODING = "utf-8"

function H($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }

function RunVal($script) {
    $o = & py -3 "tools\asset-generator\$script.py" 2>&1
    return @{ code = $LASTEXITCODE; tail = ($o | Select-Object -Last 2) -join " | " }
}

# ---------- 用例 1：只改注释必须仍绿（MetalFamily.java） ----------
$mf = "src\main\java\com\hjmmd_8\bettergold\material\MetalFamily.java"
$mfH0 = H $mf
Copy-Item $mf "$ev\_bak_MetalFamily.java" -Force
Add-Content -LiteralPath $mf -Value "`n// [bgn10-perturb] 只改注释的对照：形态子集断言读的是去注释源码`n"
$r = RunVal "validate_metal_data"
$log += "CASE1 comment-only  MetalFamily.java  => exit $($r.code)  $($r.tail)"
Copy-Item "$ev\_bak_MetalFamily.java" $mf -Force
$log += "CASE1 restore  sha256_equal=$((H $mf) -eq $mfH0)"

# ---------- 用例 2：metal_forms.py 加回 bricks（Java ↔ Python 不一致） ----------
$pyf = "tools\asset-generator\metal_forms.py"
$pyH0 = H $pyf
Copy-Item $pyf "$ev\_bak_metal_forms.py" -Force
$t = Get-Content -Raw -LiteralPath $pyf
$t2 = $t.Replace('"chaosalloy": ["ingot", "block", "upgrade_template"],',
                 '"chaosalloy": ["ingot", "block", "upgrade_template", "bricks"],')
if ($t2 -eq $t) { $log += "CASE2 PATTERN MISS" } else {
  Set-Content -NoNewline -LiteralPath $pyf -Value $t2
  $r = RunVal "validate_metal_data"
  $log += "CASE2 dirty(forms)  metal_forms.py  => exit $($r.code)  $($r.tail)"
}
Copy-Item "$ev\_bak_metal_forms.py" $pyf -Force
$log += "CASE2 restore  sha256_equal=$((H $pyf) -eq $pyH0)"

# ---------- 用例 3：前置缺失（metal_forms.py 被抽走）⇒ exit 2 ----------
Rename-Item -LiteralPath $pyf -NewName "metal_forms.py.bak"
$r = RunVal "validate_metal_data"
$log += "CASE3 missing-prereq  metal_forms.py 改名  => exit $($r.code)  $($r.tail)"
Rename-Item -LiteralPath "tools\asset-generator\metal_forms.py.bak" -NewName "metal_forms.py"
$log += "CASE3 restore  sha256_equal=$((H $pyf) -eq $pyH0)"

# ---------- 用例 4：信标基座标签里删掉 chaosalloy_block ----------
$bc = "src\main\resources\data\minecraft\tags\block\beacon_base_blocks.json"
$bcH0 = H $bc
Copy-Item $bc "$ev\_bak_beacon.json" -Force
$t = Get-Content -Raw -LiteralPath $bc
$t2 = $t -replace '\s*"bettergold:chaosalloy_block",', ''
if ($t2 -eq $t) { $log += "CASE4 PATTERN MISS" } else {
  Set-Content -NoNewline -LiteralPath $bc -Value $t2
  $r = RunVal "validate_metal_data"
  $log += "CASE4 dirty(beacon)  beacon_base_blocks.json  => exit $($r.code)  $($r.tail)"
}
Copy-Item "$ev\_bak_beacon.json" $bc -Force
$log += "CASE4 restore  sha256_equal=$((H $bc) -eq $bcH0)"

# ---------- 用例 5：删掉 chaosgold_block 的 blockstate（声明了却缺件） ----------
$bs = "src\main\resources\assets\bettergold\blockstates\chaosgold_block.json"
$bsH0 = H $bs
Copy-Item $bs "$ev\_bak_chaosgold_block.json" -Force
Remove-Item -LiteralPath $bs -Force
$r = RunVal "validate_metal_assets"
$log += "CASE5 dirty(missing-blockstate)  => exit $($r.code)  $($r.tail)"
Copy-Item "$ev\_bak_chaosgold_block.json" $bs -Force
$log += "CASE5 restore  sha256_equal=$((H $bs) -eq $bsH0)"

$log | Set-Content -Encoding utf8 "$ev\17-扰动实测.log"
$log | ForEach-Object { $_ }
