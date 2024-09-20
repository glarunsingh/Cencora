import { Component, Input } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-client-modal',
  templateUrl: './client-modal.component.html',
  styleUrls: ['./client-modal.component.scss']
})
export class ClientModalComponent {

  @Input() adminClientDetails!: any;

  public adminClientFormGrp!: FormGroup;  //defined the adminClientFormGrp
  public adminEditClientFormGroup!: FormGroup;
  public title: string = "";

  constructor(public activeModal: NgbActiveModal, private formBuilder: FormBuilder) { }

  ngOnInit() {
    this.formCheckDynamic();
  }

  formCheckDynamic() {
    if (this.adminClientDetails.type == "add") this.createAddFormHandler();
    else this.createEditFormHandler();
    this.title = this.adminClientDetails.type == "add" ? 'Add client' : 'Edit client';
  }

  /**add form func */
  createAddFormHandler() {
    this.adminClientFormGrp = this.formBuilder.group({
      items: this.formBuilder.array([this.adminClientAddForm()])
    });
  }

  adminClientAddForm() {
    return this.formBuilder.group({
      clientName: ['', Validators.required],
      synonyms: ['', Validators.required]
    })
  }

  adminClientGetControls() {
    return (this.adminClientFormGrp.get("items") as FormArray)
  }

  adminClientAddNewRow() {
    if (this.adminClientGetControls().length <= 3) this.adminClientGetControls().push(this.adminClientAddForm())
  }

  adminClientDeleteRow(index: number) {
    const control = this.adminClientGetControls();
    control.removeAt(index);
  }

  /**edit form func */

  createEditFormHandler() {
    this.adminEditClientFormGroup = this.formBuilder.group({
      clientName: ['', Validators.required],
      synonyms: ['', Validators.required]
    })
    this.adminEditClientFormGroup.patchValue(this.adminClientDetails.data)
  }

  adminEditClientGetControls() {
    return (this.adminEditClientFormGroup)
  }

  submitModal() {
    if (this.adminClientDetails.type == "add") {
      if (this.adminClientFormGrp.valid) {
        this.activeModal.close({ emitObj: this.adminClientFormGrp.value, type: "add" })
      }
    } else {
      if (this.adminEditClientFormGroup.valid) {
        this.activeModal.close({ emitObj: this.adminEditClientFormGroup.value, type: "edit" })
      }
    }
  }

  closeModal() {
    this.activeModal.close()
  }

  getImagePath(args: string) {
    if (args == "Add client") return 'assets/icons/manage-popup-add-title-icon.svg';
    return "assets/icons/pencil-1.svg";
  }

}
