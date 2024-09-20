import { Component, Input } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-feedback-modal',
  templateUrl: './feedback-modal.component.html',
  styleUrls: ['./feedback-modal.component.scss']
})
export class FeedbackModalComponent {

  @Input() article!: any;
  public challangesList: string[] = ['Irrelevant news', 'Improper summary', 'Technical issues', 'Bias in summary', 'Summary length issue', 'Inaccurate information', 'Incorrect sentiment analysis']
  public selectedChallange: string = "";
  public feedbackModalForm!: FormGroup;
  public isSubmitted: boolean = false;

  constructor(public activeModal: NgbActiveModal, private formBuilder: FormBuilder) { }

  ngOnInit() {
    this.createFeedbackForm();
  }

  createFeedbackForm() {
    this.feedbackModalForm = this.formBuilder.group({
      category: ['', Validators.required],
      comment: ['', Validators.required]
    })
  }

  get f(): { [key: string]: AbstractControl } {
    return this.feedbackModalForm.controls;
  }

  closeModal() {
    this.activeModal.close();
  }

  submitFeedback() {
    this.isSubmitted = true;
    if (this.feedbackModalForm.valid) {
      this.activeModal.close(this.feedbackModalForm.value);
    }

  }


}
