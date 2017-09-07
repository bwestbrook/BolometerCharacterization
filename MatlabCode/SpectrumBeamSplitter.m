function SpectrumBeamSplitter(file,lower,upper,eff,graphfile,option)
%close all
data = load(file);
[low_difference, low_position] = min(abs(data(:,1) - lower));
[high_difference, high_position] = min(abs(data(:,1) - upper));
data_X = data([low_position:high_position],1);
data_Y = data([low_position:high_position],2);

%atm =
%load('C:\Users\asuzuki\Documents\PolarBear\Analysis\AnalysisExamples\Data\CH_1000.out');
atm = load('E:\Suzuki\PolarBear\Analysis\AnalysisExamples\Data\CH_1000.out');
atm_X = atm(:,1);
atm_Y = atm(:,2);

%open = load('C:\Users\asuzuki\Documents\PolarBear\Analysis\AnalysisExamples\Matlab\NormData10mil-20090301.txt');
%open = load('C:\Users\asuzuki\Documents\PolarBear\Analysis\AnalysisExamples\Matlab\BeamSplitter10mil.txt');
open = load('E:\Suzuki\PolarBear\Analysis\AnalysisExamples\\Matlab\BeamSplitter10mil.txt');
open_X = open(:,1)./1e9;
open_Y = open(:,2);

data_O = interp1(open_X,open_Y,data_X);
data_D = data_Y./data_O;

%data_N = smooth(smooth(smooth(smooth(smooth(smooth(data_D))))));
data_N = data_D;
data_N = eff.*data_N/max(data_N);

plot(data_X,data_N,option);
hold on
%plot(data_X,data_O./max(data_O),'-- blue');
%plot(atm_X,atm_Y./max(atm_Y),'-- black');
grid on
xlabel('Frequency [GHz]')
ylabel('Efficiency')
title('Spectra')
axis([lower upper -0.1 1.2]);
saveas(gcf,graphfile,'fig') 
saveas(gcf,graphfile,'bmp') 
saveas(gcf,graphfile,'eps') 

