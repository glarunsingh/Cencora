import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomRadiobuttonComponent } from './custom-radiobutton.component';

describe('CustomRadiobuttonComponent', () => {
  let component: CustomRadiobuttonComponent;
  let fixture: ComponentFixture<CustomRadiobuttonComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CustomRadiobuttonComponent]
    });
    fixture = TestBed.createComponent(CustomRadiobuttonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
