import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageKeywordAdminComponent } from './manage-keyword-admin.component';

describe('ManageKeywordAdminComponent', () => {
  let component: ManageKeywordAdminComponent;
  let fixture: ComponentFixture<ManageKeywordAdminComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ManageKeywordAdminComponent]
    });
    fixture = TestBed.createComponent(ManageKeywordAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
