class nest1 {

  void func1(){
    int a = 10;
    class inner{
      void func2(){
        System.out.println(a);
      }
    }
    (new inner()).func2();
  }

  public static void main(String[] args){
    (new nest1()).func1();
  }
}
