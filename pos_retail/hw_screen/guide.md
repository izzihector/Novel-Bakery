Guide Setup POSBOX support Multi Epson Printer
----------------------------------------------

Install POSBOX 17
----------------------------------------------
- [x] Install posbox https://odoo-development.readthedocs.io/en/latest/admin/posbox/install-posbox-image.html
- [x] first for all required need to buy one Raspi Model B+ or bigger than
- [x] install posbox follow this link [a link] https://www.odoo.com/forum/help-1/question/step-by-step-guide-for-installing-customer-display-using-posbox-125783

Update POSBOX with my module
----------------------------------------------
- [x] first need ssh to posbox: $ssh pi@[iot proxy] , password is: raspberry. Example: ssh pi@192.168.1.2
- [x] Need change to root rule and Mount SD card for modifiers all files of SD card: $ sudo su && mount -o remount,rw /
- [x] Change permission of addons odoo: $cd /home/pi/odoo
- [x] $ sudo chmod 777 -R addons
- [x] Open FileZilla, copy all files of hw_screen to path foder of IOT box:  /home/pi/odoo/addons
- [x] Change script odoo iot box: vim /etc/init.d/odoo
- [x] Reboot posbox now: $ reboot now