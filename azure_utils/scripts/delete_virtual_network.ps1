$networkInterfaces = Get-AzVirtualNetwork

$networkInterfaces | ForEach-Object -Parallel {
    if ($_.name -like "capsule*") {
        echo "Deleting Virtual Network with Id: $($_.Id)"
        Remove-AzVirtualNetwork -Name $_.name -ResourceGroupName agent-eval-plaform -Force
        echo "Deleted Virtual Network with Id: $($_.Id) "
    }
} -ThrottleLimit 30