Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.disksize.size = '50GB'
  config.vm.network "forwarded_port", guest: 6379, host: 6379, auto_correct: true
  config.vm.network "forwarded_port", guest: 3306, host: 3306, auto_correct: true
  config.vm.network "forwarded_port", guest: 80, host: 80, auto_correct: true
  config.vm.synced_folder "~/data", "/data"
  config.vm.synced_folder "", "/srv/greencandle"
  config.vm.synced_folder '.', '/vagrant', disabled: true

  config.vm.provider "virtualbox" do |vb, override|
    vb.customize ['modifyvm', :id, '--cpus', ENV['VCPUS'] || 2]
    vb.customize ['modifyvm', :id, '--memory', ENV['VRAM'] || '2046']
    #vb.customize [ 'guestproperty', 'set', :id, '/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold', 10000 ]
  end

  # Bootstrap machine
  config.vm.provision :shell, :inline => "cd /srv/greencandle;bash bootstrap.sh && bash gc-install.sh"
end
