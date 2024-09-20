import { Component, Input } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-keyword-modal',
  templateUrl: './keyword-modal.component.html',
  styleUrls: ['./keyword-modal.component.scss']
})
export class KeywordModalComponent {

  @Input() adminKeywordDetails!: any;
  public adminKeywordFormGrp!: FormGroup;  //defined the adminKeywordFormGrp
  public adminEditKeyFormGroup!: FormGroup;
  public title: string = "";

  constructor(public activeModal: NgbActiveModal, private formBuilder: FormBuilder) { }

  ngOnInit() {
    this.formCheckDynamic();
  }

  formCheckDynamic() {
    if (this.adminKeywordDetails.type == "add") this.createAddFormHandler();
    else this.createEditFormHandler();
    this.title = this.adminKeywordDetails.type == "add" ? 'Add keyword' : 'Edit keyword';
  }

  /**add form func */
  createAddFormHandler() {
    this.adminKeywordFormGrp = this.formBuilder.group({
      items: this.formBuilder.array([this.adminKeywordAddForm()])
    });
  }

  adminKeywordAddForm() {
    return this.formBuilder.group({
      keyword: ['', Validators.required]
    })
  }

  adminKeyGetControls() {
    return (this.adminKeywordFormGrp.get("items") as FormArray)
  }

  adminKeywordAddNewRow() {
    if (this.adminKeyGetControls().length <= 3) this.adminKeyGetControls().push(this.adminKeywordAddForm())
  }

  adminKeywordDelRow(index: number) {
    const control = this.adminKeyGetControls();
    control.removeAt(index);
  }

  /**edit form func */

  createEditFormHandler() {
    this.adminEditKeyFormGroup = this.formBuilder.group({
      keyword: ['', Validators.required]
    })
    this.adminEditKeyFormGroup.patchValue(this.adminKeywordDetails.data)
  }

  adminEditClientGetControls() {
    return (this.adminEditKeyFormGroup)
  }

  submitModal() {
    if (this.adminKeywordDetails.type == "add") {
      if (this.adminKeywordFormGrp.valid) {
        this.activeModal.close({ emitObj: this.adminKeywordFormGrp.value, type: "add" })
      }
    } else {
      if (this.adminEditKeyFormGroup.valid) {
        this.activeModal.close({ emitObj: this.adminEditKeyFormGroup.value, type: "edit" })
      }
    }
  }

  closeModal() {
    this.activeModal.close()
  }

  getImagePath(args: string) {
    if (args == "Add keyword") return 'assets/icons/manage-popup-add-title-icon.svg';
    return "assets/icons/pencil-1.svg";
  }
}
