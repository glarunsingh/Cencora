import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent {

  @Input() deleteConfirmDetails!: any;

  constructor(public activeModal: NgbActiveModal) { }

  ngOnInit() {}

  closeModal() {
    this.activeModal.close();
  }

  confirmDelete() {
    this.activeModal.close('delete');
  }

}
