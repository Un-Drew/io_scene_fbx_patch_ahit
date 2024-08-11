If ($args.count -ne 1)
{
	Write-Host "This command requires exactly 1 parameter!!"
	Exit
}

$addonPath = $args[0]
$addonVersion = Split-Path -Path $addonPath -Leaf

# Only build if the passed in directory's name uses a semantic version format
# Regex explanation:
#     ^ and $ mark that the entire string has to match the regex
#     [0-9]+ searches for one or more digits
#     \. marks a dot
if ($addonVersion -notmatch "^[0-9]+\.[0-9]+\.[0-9]+$")
{
	Write-Host "Passed in directory $addonVersion must use a semantic version."
	Exit
}

Compress-Archive "$addonPath/io_scene_fbx_patch_ahit" "$addonPath/io_scene_fbx_patch_ahit-$addonVersion.zip" -Force

Write-Host "Success!"
