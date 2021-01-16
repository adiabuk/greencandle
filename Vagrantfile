Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.disksize.size = '50GB'
  config.vm.network :forwarded_port, guest: 22, host: 2222, id: "ssh", auto_correct: true
  config.vm.network "forwarded_port", guest: 6379, host: 63790, auto_correct: true
  config.vm.network "forwarded_port", guest: 3306, host: 33060, auto_correct: true
  config.vm.network "forwarded_port", guest: 7777, host: 7777, auto_correct: true
  config.vm.network "forwarded_port", guest: 80, host: 8080, auto_correct: true
  config.vm.synced_folder "~/data", "/data"
  config.vm.synced_folder "..//binance", "/mnt/binance"
  config.vm.synced_folder "", "/srv/greencandle"
  config.vm.synced_folder '.', '/vagrant', disabled: true

  config.vm.provider "virtualbox" do |vb, override|
    vb.customize ['modifyvm', :id, '--cpus', ENV['VCPUS'] || 2]
    vb.customize ['modifyvm', :id, '--memory', ENV['VRAM'] || '2046']
    #vb.customize [ 'guestproperty', 'set', :id, '/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold', 10000 ]
  end

  # Bootstrap machine
  config.vm.provision :shell, :inline => "cd /srv/greencandle;bash install/bootstrap_dev.sh"
end
