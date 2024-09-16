$networkInterfaces = Get-AzPublicIpAddress

$networkInterfaces | ForEach-Object -Parallel {
    if ($_.name -like "capsule*") {
        echo "Deleting Public IP with Id: $($_.Id)"
        Remove-AzPublicIpAddress -Name $_.name -ResourceGroupName agent-eval-plaform -Force
        echo "Deleted Public IP with Id: $($_.Id) "
    }
} -ThrottleLimit 30