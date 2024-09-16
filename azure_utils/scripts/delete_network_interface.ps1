$networkInterfaces = Get-AzNetworkInterface

$networkInterfaces | ForEach-Object -Parallel {
    if ($_.name -like "capsule*") {
        echo "Deleting Network Interface with Id: $($_.Id)"
        Remove-AzNetworkInterface -Name $_.name -ResourceGroupName agent-eval-plaform -Force
        echo "Deleted Network Interface with Id: $($_.Id) "
    }
} -ThrottleLimit 30