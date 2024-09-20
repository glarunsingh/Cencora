import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MegaBoxComponent } from './mega-box.component';

describe('MegaBoxComponent', () => {
  let component: MegaBoxComponent;
  let fixture: ComponentFixture<MegaBoxComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [MegaBoxComponent]
    });
    fixture = TestBed.createComponent(MegaBoxComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
