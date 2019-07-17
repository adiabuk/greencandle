Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.disksize.size = '50GB'

  # Bootstrap machine
  #config.vm.provision :shell, :inline => "bash bootstrap.sh"
  config.vm.provider "virtualbox" do |vb, override|
    vb.customize ['modifyvm', :id, '--cpus', ENV['VCPUS'] || 2]
    vb.customize ['modifyvm', :id, '--memory', ENV['VRAM'] || '2046']
    vb.customize [ 'guestproperty', 'set', :id, '/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold', 10000 ]
  end
end
