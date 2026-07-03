// Copyright (c) 2020 madVR Labs, LLC. All rights reserved.

// Permission is hereby granted to use this sample and make
// derivative works therefore, for use in conjunction with
// the madVR Envy hardware and software.

program EnvyIpControl;

uses
  madExcept,
  madLinkDisAsm,
  madListHardware,
  madListProcesses,
  madListModules,
  Forms,
  EnvyIpControlMainForm in 'EnvyIpControlMainForm.pas' {FEnvyIpControlMainForm},
  EnvyIpControlSlotBox in 'EnvyIpControlSlotBox.pas' {SlotBox};

{$R mad.res}
{$R comctl6.res}
{$R EnvyIpControlVersion.res}

begin
  Application.Initialize;
  Application.CreateForm(TFEnvyIpControlMainForm, FEnvyIpControlMainForm);
  Application.Run;
end.
