function BeamSplitter(t,n,f_l,f_h)
close all
f = [f_l:(f_h-f_l)/10000.:f_h];
R = (n-1)^2/(n+1)^2;
c = 3e8;
eff = 8*(1-R)^2*R*(cos(2*pi*(f/c*t*sqrt(n^2-0.5)+0.25))).^2;


plot(f,eff,'-r');
grid on
xlabel('Frequency [Hz]')
ylabel('Efficiency')
title('BeamSplitter')

%saveas(gcf,graphfile,'jpg') 
%saveas(gcf,graphfile,'eps') 

