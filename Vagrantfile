Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"

  # Bootstrap machine
  config.vm.provision :shell, :inline => "apt-get update -y"
  config.vm.provision :shell, :inline => "bash install.sh"

  config.vm.provider "virtualbox" do |vb, override|
    vb.customize ['modifyvm', :id, '--cpus', ENV['VCPUS'] || 2]
    vb.customize ['modifyvm', :id, '--memory', ENV['VRAM'] || '2046']
  end
end
