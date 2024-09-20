import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KeywordModalComponent } from './keyword-modal.component';

describe('KeywordModalComponent', () => {
  let component: KeywordModalComponent;
  let fixture: ComponentFixture<KeywordModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [KeywordModalComponent]
    });
    fixture = TestBed.createComponent(KeywordModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
