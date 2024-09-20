import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonalizeComponent } from './personalize.component';

describe('PersonalizeComponent', () => {
  let component: PersonalizeComponent;
  let fixture: ComponentFixture<PersonalizeComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PersonalizeComponent]
    });
    fixture = TestBed.createComponent(PersonalizeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
