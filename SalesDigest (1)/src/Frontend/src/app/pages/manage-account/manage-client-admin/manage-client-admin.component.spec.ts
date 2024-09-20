import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageClientAdminComponent } from './manage-client-admin.component';

describe('ManageClientAdminComponent', () => {
  let component: ManageClientAdminComponent;
  let fixture: ComponentFixture<ManageClientAdminComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ManageClientAdminComponent]
    });
    fixture = TestBed.createComponent(ManageClientAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
