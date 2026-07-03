// Copyright (c) 2020 madVR Labs, LLC. All rights reserved.

// Permission is hereby granted to use this sample and make
// derivative works therefore, for use in conjunction with
// the madVR Envy hardware and software.

unit EnvyIpControlSlotBox;

interface

uses
  Winapi.Windows, Winapi.Messages, System.SysUtils, System.Variants, System.Classes, Vcl.Graphics,
  Vcl.Controls, Vcl.Forms, Vcl.Dialogs, Vcl.ExtCtrls, Vcl.StdCtrls;

type
  TSlotBox = class(TForm)
    OkButton: TButton;
    CancelButton: TButton;
    GroupBox1: TGroupBox;
    SlotPanel: TPanel;
    SlotLabel: TLabel;
    SlotCombo: TComboBox;
    PasswordPanel: TPanel;
    PasswordLabel: TLabel;
    PasswordEdit: TEdit;
    NamePanel: TPanel;
    NameLabel: TLabel;
    NameEdit: TEdit;
    procedure UpdateButtons(Sender: TObject);
    procedure FormKeyPress(Sender: TObject; var Key: Char);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

function DoSlotNameBox(const title, slotLabelText, nameLabelText, slots: string; var slot: integer; var name: string) : boolean;
function DoSlotBox(const title, slotLabelText, slots: string; var slot: integer) : boolean;
function DoNameBox(const title, nameLabelText: string; var name: string) : boolean;
function DoNamePasswordBox(const title, nameLabelText: string; var name, password: string) : boolean;

implementation

{$R *.dfm}

uses madStrings;

function DoBoxInternal(const title, slotLabelText, nameLabelText, slots: string; showSlot, showName, showPassword: boolean; var slot: integer; var name_, password: string) : boolean;
var i1 : integer;
    s1 : string;
begin
  with TSlotBox.Create(nil) do begin
    Caption := title;
    SlotLabel.Caption := slotLabelText;
    NameLabel.Caption := nameLabelText;
    SlotCombo.Items.Clear;
    for i1 := 1 to SubStrCount(slots) do begin
      s1 := SubStr(slots, i1);
      if s1[1] = '!' then begin
        SlotCombo.Items.Add(Copy(s1, 2, maxInt));
        SlotCombo.ItemIndex := i1 - 1;
      end else
        SlotCombo.Items.Add(s1);
    end;
    if SlotCombo.ItemIndex = -1 then
      SlotCombo.ItemIndex := 0;
    if not showSlot then begin
      Height := Height - SlotPanel.Height;
      SlotPanel.Visible := false;
    end;
    if not showName then begin
      Height := Height - NamePanel.Height;
      NamePanel.Visible := false;
    end;
    if not showPassword then begin
      Height := Height - PasswordPanel.Height;
      PasswordPanel.Visible := false;
    end;
    NameEdit.Text := name_;
    PasswordEdit.Text := password;
    UpdateButtons(nil);
    result := ShowModal = mrOk;
    slot := SlotCombo.ItemIndex + 1;
    name_ := NameEdit.Text;
    password := PasswordEdit.Text;
    Free;
  end;
end;

function DoSlotNameBox(const title, slotLabelText, nameLabelText, slots: string; var slot: integer; var name: string) : boolean;
var s1 : string;
begin
  s1 := '';
  result := DoBoxInternal(title, slotLabelText, nameLabelText, slots, true, true, false, slot, name, s1);
end;

function DoSlotBox(const title, slotLabelText, slots: string; var slot: integer) : boolean;
var s1, s2 : string;
begin
  s1 := '';
  s2 := '';
  result := DoBoxInternal(title, slotLabelText, '', slots, true, false, false, slot, s1, s2);
end;

function DoNameBox(const title, nameLabelText: string; var name: string) : boolean;
var i1 : integer;
    s1 : string;
begin
  s1 := '';
  result := DoBoxInternal(title, '', nameLabelText, '', false, true, false, i1, name, s1);
end;

function DoNamePasswordBox(const title, nameLabelText: string; var name, password: string) : boolean;
var i1 : integer;
begin
  result := DoBoxInternal(title, '', nameLabelText, '', false, true, true, i1, name, password);
end;

procedure TSlotBox.UpdateButtons(Sender: TObject);
begin
  OkButton.Enabled := ((not     NamePanel.Visible) or ((    NameEdit.Text <> '') and (NameEdit.Text[1] <> '!'))) and
                      ((not PasswordPanel.Visible) or  (PasswordEdit.Text <> ''));
end;

procedure TSlotBox.FormKeyPress(Sender: TObject; var Key: Char);
begin
  if (Key = #13) and OkButton.Enabled then begin
    Key := #0;
    ModalResult := mrOk;
  end;
end;

end.
