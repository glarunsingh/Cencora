import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonService } from './common.service';
import { environment } from 'src/environments/environment';

interface apiResponse {
  message: string;
  data: any
  status: string,
  success: string | boolean
}


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  public api_url: string = environment.api_url;

  constructor(private http: HttpClient, public commonService: CommonService) { }

  //Authorization: Bearer token
  createAuthorizationHeader(): HttpHeaders {
    return new HttpHeaders({
      'Authorization': 'Bearer ' + '' + atob(this.commonService.getStorageItems('raw')),
      'Content-Type': 'application/json'
    })
  }

  getInitialRoles(): Observable<apiResponse> {
    return this.http.get<apiResponse>(this.api_url + "onboarding/init", { headers: this.createAuthorizationHeader() })
  }

  getDrugChannelData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "fetch_dc_data", payload, { headers: this.createAuthorizationHeader() })
  }

  downloadDrugChannelData(timeStampsList: any): Observable<Blob> {
    return this.http.post(this.api_url + "main_app/download_excel", timeStampsList, { headers: this.createAuthorizationHeader(), responseType: 'blob' })
  }

  getDepartmentList(): Observable<apiResponse> {
    return this.http.get<apiResponse>(this.api_url + "onboarding/get_departments", { headers: this.createAuthorizationHeader() })
  }

  getClientNamesList(args: string) {
    return this.http.get(this.api_url + "onboarding/get_clients_name/" + '' + args, { headers: this.createAuthorizationHeader() })
  }

  sendUserOnBoardinDetails(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/user_details", payload, { headers: this.createAuthorizationHeader() })
  }

  getClientNewsClientList(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/fetch_client", payload, { headers: this.createAuthorizationHeader() })
  }

  getDeinitiveClienList(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/fetch_definitive_client", payload, { headers: this.createAuthorizationHeader() })
  }

  getBreakingNews(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/breaking_news", payload, { headers: this.createAuthorizationHeader() })
  }

  getClientNewsUpdateData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/source_data", payload, { headers: this.createAuthorizationHeader() })
  }

  downloadClientNewsData(payload: any): Observable<Blob> {
    return this.http.post(this.api_url + "main_app/download_excel", payload, { headers: this.createAuthorizationHeader(), responseType: 'blob' })
  }

  downloadDefinitiveData(payload: any): Observable<Blob> {
    return this.http.post(this.api_url + "main_app/download_definitive_excel", payload, { headers: this.createAuthorizationHeader(), responseType: 'blob' })
  }

  getDeinitiveChannelData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/definitive_data", payload, { headers: this.createAuthorizationHeader() })
  }

  fetchnonAdminClientListData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/fetch_client_non_admin_manage", payload, { headers: this.createAuthorizationHeader() })
  }

  saveUnsaveNonAdminFavClients(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/non_admin_save_fav_client", payload, { headers: this.createAuthorizationHeader() })
  }

  fetchAdminClientListData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/fetch_admin_client", payload, { headers: this.createAuthorizationHeader() })
  }

  saveAdminClientListData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/admin_save_client_modification", payload, { headers: this.createAuthorizationHeader() })
  }

  deleteAdminClientRow(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/delete_client_admin", payload, { headers: this.createAuthorizationHeader() })
  }

  fetchAdminKeywordListData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "main_app/fetch_admin_keywords", payload, { headers: this.createAuthorizationHeader() })
  }

  saveAdminKeywordListData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/admin_save_keywords_modification", payload, { headers: this.createAuthorizationHeader() })
  }

  deleteAdminKeywordRow(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "onboarding/delete_keywords_admin", payload, { headers: this.createAuthorizationHeader() })
  }

  updateFeedback(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "feedback/update_user_feedback", payload, { headers: this.createAuthorizationHeader() })
  }

  fetchKeywords(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "keyword_digest/fetch_keywords", payload, { headers: this.createAuthorizationHeader() })
  }

  getKeywordSearchData(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "keyword_digest/get_search_data", payload, { headers: this.createAuthorizationHeader() })
  }

  getKeywordSummary(payload: any): Observable<apiResponse> {
    return this.http.post<apiResponse>(this.api_url + "keyword_digest/get_keyword_summary", payload, { headers: this.createAuthorizationHeader() })
  }

  downloadKeyworsDigestData(payload: any): Observable<Blob> {
    return this.http.post(this.api_url + "keyword_digest/download_searched_news_excel", payload, { headers: this.createAuthorizationHeader(), responseType: 'blob' })
  }

  getUserProfileDetails(cbs: any, cbe: any) {
    this.http.get("https://graph.microsoft.com/v1.0/me").subscribe((response) => {
      cbs(response);
    }, (error: HttpErrorResponse) => {
      cbe(error['name'] + ' : ' + error['statusText'])
    })
  }

}
