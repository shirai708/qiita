class nest2 {

  void func1(){
    int a = 10;
    class inner{
      void func2(){
        a = 20;
      }
    }
    (new inner()).func2();
  }

  public static void main(String[] args){
    (new nest2()).func1();
  }
}
