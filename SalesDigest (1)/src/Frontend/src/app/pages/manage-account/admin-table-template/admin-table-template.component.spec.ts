import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminTableTemplateComponent } from './admin-table-template.component';

describe('AdminTableTemplateComponent', () => {
  let component: AdminTableTemplateComponent;
  let fixture: ComponentFixture<AdminTableTemplateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AdminTableTemplateComponent]
    });
    fixture = TestBed.createComponent(AdminTableTemplateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
