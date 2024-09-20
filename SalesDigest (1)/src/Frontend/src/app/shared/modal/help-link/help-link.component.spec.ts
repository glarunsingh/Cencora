import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HelpLinkComponent } from './help-link.component';

describe('HelpLinkComponent', () => {
  let component: HelpLinkComponent;
  let fixture: ComponentFixture<HelpLinkComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [HelpLinkComponent]
    });
    fixture = TestBed.createComponent(HelpLinkComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
