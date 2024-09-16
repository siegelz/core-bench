$managedDisks = Get-AzDisk

$managedDisks | ForEach-Object -Parallel {
    # ManagedBy property stores the Id of the VM to which Managed Disk is attached to
    # If ManagedBy property is $null then it means that the Managed Disk is not attached to a VM
    if($_.ManagedBy -eq $null){
        echo "Deleting unattached Managed Disk with Id: $($_.Id)"
        $_ | Remove-AzDisk -Force
        echo "Deleted unattached Managed Disk with Id: $($_.Id) "
    }
} -ThrottleLimit 30